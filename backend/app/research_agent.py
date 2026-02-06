"""
Research Agent: Extracts financial data using Composio MCP
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

try:
    from composio import ComposioToolset, Action, App
    from composio.client import ComposioClient
    COMPOSIO_AVAILABLE = True
except ImportError:
    COMPOSIO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Composio not available. Install with: pip install composio-core")

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Agent that extracts financial data from multiple sources using Composio."""
    
    def __init__(self, composio_api_key: str):
        """Initialize Research Agent with Composio client."""
        if not COMPOSIO_AVAILABLE:
            raise ImportError("Composio is not installed. Install with: pip install composio-core")
        self.client = ComposioClient(api_key=composio_api_key)
        self.toolset = ComposioToolset()
        
    async def extract_from_xero(
        self, 
        connection_id: str,
        tenant_id: str
    ) -> List[Dict]:
        """
        Extract loan data from Xero.
        
        Args:
            connection_id: Xero OAuth connection ID
            tenant_id: Xero tenant ID
            
        Returns:
            List of transactions/contracts converted to loan format
        """
        try:
            # Connect to Xero using Composio
            xero_app = App.XERO
            connection = self.client.get_connection(
                entity_id=connection_id,
                app=xero_app
            )
            
            # Extract contacts (clients) and invoices
            contacts = await self.toolset.execute_action(
                action=Action.XERO_GET_CONTACTS,
                connection=connection,
                params={"tenant_id": tenant_id}
            )
            
            # Extract financial transactions
            transactions = await self.toolset.execute_action(
                action=Action.XERO_GET_TRANSACTIONS,
                connection=connection,
                params={"tenant_id": tenant_id}
            )
            
            # Convert to LoanRecord format
            loans = self._convert_xero_to_loans(contacts, transactions)
            logger.info(f"Extracted {len(loans)} loans from Xero")
            return loans
            
        except Exception as e:
            logger.error(f"Error extracting from Xero: {e}")
            raise
    
    async def extract_from_quickbooks(
        self,
        connection_id: str,
        company_id: str
    ) -> List[Dict]:
        """
        Extract loan data from QuickBooks.
        
        Args:
            connection_id: QuickBooks OAuth connection ID
            company_id: QuickBooks company ID
            
        Returns:
            List of loans in standardized format
        """
        try:
            quickbooks_app = App.QUICKBOOKS
            connection = self.client.get_connection(
                entity_id=connection_id,
                app=quickbooks_app
            )
            
            # Extract accounts receivable (AR = loans)
            accounts_receivable = await self.toolset.execute_action(
                action=Action.QUICKBOOKS_GET_ACCOUNTS_RECEIVABLE,
                connection=connection,
                params={"company_id": company_id}
            )
            
            # Extract loan transactions
            loans_data = await self.toolset.execute_action(
                action=Action.QUICKBOOKS_GET_LOANS,
                connection=connection,
                params={"company_id": company_id}
            )
            
            loans = self._convert_quickbooks_to_loans(accounts_receivable, loans_data)
            logger.info(f"Extracted {len(loans)} loans from QuickBooks")
            return loans
            
        except Exception as e:
            logger.error(f"Error extracting from QuickBooks: {e}")
            raise
    
    async def extract_from_stripe(
        self,
        connection_id: str
    ) -> List[Dict]:
        """
        Extract loan/financing data from Stripe.
        
        Args:
            connection_id: Stripe connection ID
            
        Returns:
            List of loans converted from Stripe
        """
        try:
            stripe_app = App.STRIPE
            connection = self.client.get_connection(
                entity_id=connection_id,
                app=stripe_app
            )
            
            # Extract balances and transactions
            balance = await self.toolset.execute_action(
                action=Action.STRIPE_GET_BALANCE,
                connection=connection
            )
            
            # Extract customer payment methods (may represent loans)
            customers = await self.toolset.execute_action(
                action=Action.STRIPE_GET_CUSTOMERS,
                connection=connection
            )
            
            loans = self._convert_stripe_to_loans(customers, balance)
            logger.info(f"Extracted {len(loans)} loans from Stripe")
            return loans
            
        except Exception as e:
            logger.error(f"Error extracting from Stripe: {e}")
            raise
    
    def _convert_xero_to_loans(self, contacts: List, transactions: List) -> List[Dict]:
        """Convert Xero data to LoanRecord format."""
        loans = []
        # Xero-specific conversion logic
        # Map contacts and transactions to loans
        for contact in contacts:
            # Find related transactions
            related_transactions = [
                t for t in transactions 
                if t.get('contact_id') == contact.get('id')
            ]
            
            for trans in related_transactions:
                loan = {
                    'loanId': f"XERO_{contact.get('id')}_{trans.get('id')}",
                    'borrower': contact.get('name', 'Unknown'),
                    'industry': contact.get('industry', 'general'),
                    'interestType': self._infer_interest_type(trans),
                    'principalAmount': float(trans.get('total', 0)),
                    'outstandingBalance': float(trans.get('amount_due', 0)),
                    'maturityDate': self._parse_date(trans.get('due_date')),
                    'covenants': []
                }
                loans.append(loan)
        
        return loans
    
    def _convert_quickbooks_to_loans(self, ar_data: List, loans_data: List) -> List[Dict]:
        """Convert QuickBooks data to LoanRecord format."""
        loans = []
        # QuickBooks conversion logic
        for loan_item in loans_data:
            loan = {
                'loanId': f"QB_{loan_item.get('id')}",
                'borrower': loan_item.get('customer_name', 'Unknown'),
                'industry': loan_item.get('industry', 'general'),
                'interestType': loan_item.get('interest_type', 'Cash'),
                'principalAmount': float(loan_item.get('principal', 0)),
                'outstandingBalance': float(loan_item.get('balance', 0)),
                'maturityDate': self._parse_date(loan_item.get('maturity_date')),
                'covenants': loan_item.get('covenants', [])
            }
            loans.append(loan)
        
        return loans
    
    def _convert_stripe_to_loans(self, customers: List, balance: Dict) -> List[Dict]:
        """Convert Stripe data to LoanRecord format."""
        loans = []
        # Stripe generally doesn't handle loans directly
        # But we can map pending balances as loans
        for customer in customers:
            if customer.get('balance', 0) > 0:
                loan = {
                    'loanId': f"STRIPE_{customer.get('id')}",
                    'borrower': customer.get('name', customer.get('email', 'Unknown')),
                    'industry': 'general',
                    'interestType': 'Cash',
                    'principalAmount': float(customer.get('balance', 0)),
                    'outstandingBalance': float(customer.get('balance', 0)),
                    'maturityDate': datetime.now(),  # Stripe doesn't have maturity dates
                    'covenants': []
                }
                loans.append(loan)
        
        return loans
    
    def _infer_interest_type(self, transaction: Dict) -> str:
        """Infer interest type from transaction data."""
        # Logic to determine if it's PIK, Cash or Hybrid
        description = transaction.get('description', '').lower()
        if 'pik' in description or 'payment-in-kind' in description:
            return 'PIK'
        elif 'hybrid' in description:
            return 'Hybrid'
        else:
            return 'Cash'
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Parse date from string."""
        if not date_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
