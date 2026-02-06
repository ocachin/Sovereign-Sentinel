"""
Main FastAPI application for Sovereign Sentinel backend.
"""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.you_client import YouAPIClient
from app.osint_scout import OSINTScout
from app.scheduler import ScanScheduler
from app.models import RiskAssessment, LoanRecord
from app.research_agent import ResearchAgent
from app.financial_analysis_agent import FinancialAnalysisAgent
from app.forensic_auditor import ForensicAuditor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
you_client: YouAPIClient = None
osint_scout: OSINTScout = None
scheduler: ScanScheduler = None
research_agent: ResearchAgent = None
financial_agent: FinancialAnalysisAgent = None
forensic_auditor: ForensicAuditor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    global you_client, osint_scout, scheduler, research_agent, financial_agent, forensic_auditor
    
    logger.info("Starting Sovereign Sentinel backend...")
    
    # Initialize You.com client
    you_client = YouAPIClient(api_key=settings.you_api_key)
    logger.info("You.com API client initialized")
    
    # Initialize OSINT Scout
    osint_scout = OSINTScout(you_client=you_client)
    logger.info("OSINT Scout initialized")
    
    # Initialize and start scheduler
    scheduler = ScanScheduler(osint_scout=osint_scout)
    scheduler.start()
    logger.info("Scheduler started")
    
    # Initialize Research Agent (Composio)
    if settings.composio_api_key:
        try:
            research_agent = ResearchAgent(composio_api_key=settings.composio_api_key)
            logger.info("Research Agent (Composio) initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Research Agent: {e}")
    else:
        logger.warning("COMPOSIO_API_KEY not set, Research Agent disabled")
    
    # Initialize Financial Analysis Agent
    try:
        financial_agent = FinancialAnalysisAgent()
        logger.info("Financial Analysis Agent initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Financial Analysis Agent: {e}")
        financial_agent = None
    
    # Initialize Forensic Auditor
    forensic_auditor = ForensicAuditor()
    logger.info("Forensic Auditor initialized")
    
    # Run initial scan
    try:
        await scheduler.run_immediate_scan()
        logger.info("Initial scan completed")
    except Exception as e:
        logger.error(f"Initial scan failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sovereign Sentinel backend...")
    if scheduler:
        scheduler.stop()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Sovereign Sentinel API",
    description="Financial War Room system for detecting Shadow Defaults",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Sovereign Sentinel API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.is_running if scheduler else False,
        "environment": settings.environment,
        "research_agent_available": research_agent is not None,
        "financial_agent_available": financial_agent is not None
    }


@app.get("/api/risk/latest", response_model=RiskAssessment)
async def get_latest_risk_assessment():
    """
    Get the latest risk assessment.
    
    Returns:
        Latest RiskAssessment object
    """
    if not osint_scout:
        raise HTTPException(status_code=503, detail="OSINT Scout not initialized")
    
    assessment = osint_scout.get_latest_assessment()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="No risk assessment available")
    
    return assessment


@app.post("/api/scan/immediate", response_model=RiskAssessment)
async def trigger_immediate_scan():
    """
    Trigger an immediate OSINT scan.
    
    Returns:
        RiskAssessment from the scan
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    try:
        await scheduler.run_immediate_scan()
        assessment = osint_scout.get_latest_assessment()
        
        if not assessment:
            raise HTTPException(status_code=500, detail="Scan completed but no assessment available")
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error during immediate scan: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.get("/api/scan/status")
async def get_scan_status():
    """
    Get the status of the scanning scheduler.
    
    Returns:
        Scheduler status information
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    return {
        "is_running": scheduler.is_running,
        "interval_minutes": settings.scan_interval_minutes,
        "latest_assessment_available": osint_scout.get_latest_assessment() is not None
    }


@app.post("/api/research/extract")
async def extract_financial_data(
    source: str,  # "xero" | "quickbooks" | "stripe"
    connection_id: str,
    tenant_id: Optional[str] = None
):
    """
    Extract financial data from external source using Research Agent.
    
    Args:
        source: Data source ("xero", "quickbooks", "stripe")
        connection_id: OAuth connection ID
        tenant_id: Tenant ID (required for Xero and QuickBooks)
    """
    if not research_agent:
        raise HTTPException(
            status_code=503, 
            detail="Research Agent not initialized. Set COMPOSIO_API_KEY in environment."
        )
    
    try:
        if source == "xero":
            if not tenant_id:
                raise HTTPException(400, "tenant_id required for Xero")
            loans_data = await research_agent.extract_from_xero(connection_id, tenant_id)
        elif source == "quickbooks":
            if not tenant_id:
                raise HTTPException(400, "tenant_id required for QuickBooks")
            loans_data = await research_agent.extract_from_quickbooks(connection_id, tenant_id)
        elif source == "stripe":
            loans_data = await research_agent.extract_from_stripe(connection_id)
        else:
            raise HTTPException(400, f"Unsupported source: {source}. Use 'xero', 'quickbooks', or 'stripe'")
        
        return {
            "source": source,
            "loans": loans_data,
            "count": len(loans_data),
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting data from {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/analyze")
async def analyze_portfolio(
    loans: List[LoanRecord],
    use_ai: bool = True
):
    """
    Analyze loan portfolio using Financial Analysis Agent or Forensic Auditor.
    
    Args:
        loans: List of loans to analyze
        use_ai: If True, uses Financial Analysis Agent, if False uses traditional Forensic Auditor
    """
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Financial Analysis Agent not initialized")
    
    try:
        # Get current risk context
        latest_assessment = osint_scout.get_latest_assessment() if osint_scout else None
        risk_context = {
            "global_risk_score": latest_assessment.global_risk_score if latest_assessment else 0,
            "affected_sectors": latest_assessment.affected_sectors if latest_assessment else [],
            "sentiment": latest_assessment.sentiment if latest_assessment else "neutral",
            "correlated_event": "Current geopolitical events"
        }
        
        if use_ai and financial_agent:
            # Usar Financial Analysis Agent
            flagged = await financial_agent.analyze_portfolio(loans, risk_context)
        else:
            # Usar Forensic Auditor tradicional
            flagged = forensic_auditor.flag_high_risk_loans(
                loans,
                risky_sectors=["energy", "currency", "sovereign debt"],
                correlated_event=risk_context.get("correlated_event", "Geopolitical crisis")
            )
        
        # Rankear por exposición
        ranked = forensic_auditor.rank_by_exposure(flagged)
        
        return {
            "total_loans": len(loans),
            "flagged_count": len(flagged),
            "analysis_method": "ai" if use_ai else "traditional",
            "flagged_loans": [loan.model_dump() for loan in ranked]
        }
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/analyze-and-extract")
async def extract_and_analyze(
    source: str,
    connection_id: str,
    tenant_id: Optional[str] = None,
    use_ai: bool = True
):
    """
    Combined endpoint: extracts data and analyzes it in a single step.
    
    Args:
        source: Data source ("xero", "quickbooks", "stripe")
        connection_id: OAuth connection ID
        tenant_id: Tenant ID (required for Xero and QuickBooks)
        use_ai: If True, uses Financial Analysis Agent, if False uses Forensic Auditor
    """
    if not research_agent:
        raise HTTPException(status_code=503, detail="Research Agent not initialized")
    
    try:
        # Extract data
        if source == "xero":
            if not tenant_id:
                raise HTTPException(400, "tenant_id required for Xero")
            loans_data = await research_agent.extract_from_xero(connection_id, tenant_id)
        elif source == "quickbooks":
            if not tenant_id:
                raise HTTPException(400, "tenant_id required for QuickBooks")
            loans_data = await research_agent.extract_from_quickbooks(connection_id, tenant_id)
        elif source == "stripe":
            loans_data = await research_agent.extract_from_stripe(connection_id)
        else:
            raise HTTPException(400, f"Unsupported source: {source}")
        
        # Convertir a LoanRecord objects
        loans = [LoanRecord(**loan) for loan in loans_data]
        
        # Analyze
        latest_assessment = osint_scout.get_latest_assessment() if osint_scout else None
        risk_context = {
            "global_risk_score": latest_assessment.global_risk_score if latest_assessment else 0,
            "affected_sectors": latest_assessment.affected_sectors if latest_assessment else [],
            "sentiment": latest_assessment.sentiment if latest_assessment else "neutral",
            "correlated_event": "Current geopolitical events"
        }
        
        if use_ai and financial_agent:
            flagged = await financial_agent.analyze_portfolio(loans, risk_context)
        else:
            flagged = forensic_auditor.flag_high_risk_loans(
                loans,
                risky_sectors=["energy", "currency", "sovereign debt"],
                correlated_event=risk_context.get("correlated_event", "Geopolitical crisis")
            )
        
        ranked = forensic_auditor.rank_by_exposure(flagged)
        
        return {
            "source": source,
            "extracted_count": len(loans),
            "flagged_count": len(flagged),
            "analysis_method": "ai" if use_ai else "traditional",
            "flagged_loans": [loan.model_dump() for loan in ranked]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract and analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
