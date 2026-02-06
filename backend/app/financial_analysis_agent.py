"""
Financial Analysis Agent: Analyzes financial data using rules and heuristics
"""
import logging
from typing import List, Dict
from datetime import datetime
from app.models import LoanRecord, FlaggedLoan

logger = logging.getLogger(__name__)


class FinancialAnalysisAgent:
    """
    Agent that analyzes financial data using rules and heuristics.
    Analyzes loans based on interest type, balance, and risk context.
    """
    
    def __init__(self):
        """Initialize Financial Analysis Agent."""
        logger.info("Financial Analysis Agent initialized")
    
    async def analyze_loan(
        self,
        loan: LoanRecord,
        risk_context: Dict
    ) -> Dict:
        """
        Analyze an individual loan.
        
        Args:
            loan: Loan record to analyze
            risk_context: Current geopolitical risk context
            
        Returns:
            Dictionary with loan analysis
        """
        return self._analyze_loan_logic(loan, risk_context)
    
    async def analyze_portfolio(
        self,
        loans: List[LoanRecord],
        risk_context: Dict
    ) -> List[FlaggedLoan]:
        """
        Analyze a complete loan portfolio.
        
        Args:
            loans: List of loans to analyze
            risk_context: Geopolitical risk context
            
        Returns:
            List of loans flagged as high risk
        """
        flagged_loans = []
        
        for loan in loans:
            analysis = self._analyze_loan_logic(loan, risk_context)
            
            # If analysis indicates high or critical risk, flag the loan
            if analysis.get('risk_level') in ['high', 'critical']:
                flagged_loan = FlaggedLoan(
                    **loan.model_dump(),
                    flag_reason=analysis.get('recommendation', 'High risk detected by analysis'),
                    risk_level=analysis.get('risk_level', 'medium'),
                    correlated_event=risk_context.get('correlated_event', 'Geopolitical risk'),
                    flagged_at=datetime.utcnow()
                )
                flagged_loans.append(flagged_loan)
        
        logger.info(f"Flagged {len(flagged_loans)} loans out of {len(loans)}")
        return flagged_loans
    
    def _analyze_loan_logic(self, loan: LoanRecord, risk_context: Dict) -> Dict:
        """Loan analysis logic based on rules."""
        risk_level = "low"
        risk_factors = []
        
        # Factor 1: PIK interest type
        if loan.interest_type == 'PIK':
            risk_level = "high"
            risk_factors.append("PIK interest type")
        
        # Factor 2: High outstanding balance
        if loan.outstanding_balance > 10_000_000:
            risk_level = "critical" if risk_level == "high" else "high"
            risk_factors.append("High outstanding balance")
        elif loan.outstanding_balance > 5_000_000:
            if risk_level == "low":
                risk_level = "medium"
            risk_factors.append("Moderate outstanding balance")
        
        # Factor 3: High global risk score
        global_risk_score = risk_context.get('global_risk_score', 0)
        if global_risk_score > 70:
            if risk_level == "low":
                risk_level = "medium"
            elif risk_level == "medium":
                risk_level = "high"
            risk_factors.append(f"High global risk score ({global_risk_score})")
        
        # Factor 4: Affected sectors
        affected_sectors = risk_context.get('affected_sectors', [])
        if loan.industry.lower() in [s.lower() for s in affected_sectors]:
            if risk_level == "low":
                risk_level = "medium"
            elif risk_level == "medium":
                risk_level = "high"
            risk_factors.append(f"Industry affected by geopolitical events: {loan.industry}")
        
        # Factor 5: Critical sentiment
        sentiment = risk_context.get('sentiment', 'neutral')
        if sentiment == 'critical':
            if risk_level in ["low", "medium"]:
                risk_level = "high"
            risk_factors.append("Critical geopolitical sentiment")
        
        # Generate recommendation
        recommendation = self._generate_recommendation(loan, risk_level, risk_factors)
        
        # Calculate shadow default probability
        shadow_default_probability = self._calculate_shadow_default_probability(
            risk_level, loan, risk_context
        )
        
        logger.debug(f"Analyzed loan {loan.loan_id}: {risk_level}")
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "is_pik_risk": loan.interest_type == 'PIK',
            "shadow_default_probability": shadow_default_probability
        }
    
    def _generate_recommendation(
        self, 
        loan: LoanRecord, 
        risk_level: str, 
        risk_factors: List[str]
    ) -> str:
        """Generate a recommendation based on analysis."""
        if risk_level == "critical":
            return f"CRITICAL: {loan.borrower} has PIK loan with {loan.outstanding_balance:,.0f} outstanding. Immediate review required."
        elif risk_level == "high":
            return f"HIGH RISK: {loan.borrower} - {', '.join(risk_factors[:2])}. Review recommended."
        elif risk_level == "medium":
            return f"MEDIUM RISK: {loan.borrower} - Monitor closely."
        else:
            return f"LOW RISK: {loan.borrower} - Standard monitoring."
    
    def _calculate_shadow_default_probability(
        self,
        risk_level: str,
        loan: LoanRecord,
        risk_context: Dict
    ) -> float:
        """Calculate shadow default probability."""
        base_probability = {
            "low": 0.05,
            "medium": 0.15,
            "high": 0.35,
            "critical": 0.60
        }.get(risk_level, 0.1)
        
        # Adjust by interest type
        if loan.interest_type == 'PIK':
            base_probability += 0.15
        
        # Adjust by balance
        if loan.outstanding_balance > 10_000_000:
            base_probability += 0.10
        
        # Adjust by global risk
        global_risk_score = risk_context.get('global_risk_score', 0)
        if global_risk_score > 70:
            base_probability += 0.10
        
        # Limit to maximum 0.95
        return min(base_probability, 0.95)
