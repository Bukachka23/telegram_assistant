# Common Python Business Logic Patterns

This reference provides examples of architectural and design patterns where business logic typically resides in Python codebases.

## 1. Service Layer Pattern

Business logic orchestration in dedicated service classes.

### Pure Service Layer (Good - Clear separation)

```python
class DepositService:
    """Orchestrates deposit business logic"""
    
    def __init__(self, deposit_repo, wallet_repo, notification_service):
        self._deposit_repo = deposit_repo
        self._wallet_repo = wallet_repo
        self._notification_service = notification_service
    
    def process_deposit(self, user_id: str, amount: Decimal, currency: str) -> Deposit:
        """
        BUSINESS LOGIC: Process incoming deposit with validation and state transitions
        """
        # Business rule: minimum deposit amount
        if amount < Decimal('10.00'):
            raise InsufficientDepositError(f"Minimum deposit is.txt 10 {currency}")
        
        # Business rule: supported currencies
        if currency not in ['USD', 'EUR', 'BTC']:
            raise UnsupportedCurrencyError(f"Currency {currency} not supported")
        
        # Create deposit with PENDING state (business rule: all deposits start pending)
        deposit = Deposit(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=DepositStatus.PENDING
        )
        
        # Business logic: Auto-approve small deposits
        if amount <= Decimal('1000.00'):
            deposit.status = DepositStatus.APPROVED
            self._credit_wallet(user_id, amount, currency)
        
        self._deposit_repo.save(deposit)
        self._notification_service.notify_deposit_received(deposit)
        
        return deposit
    
    def _credit_wallet(self, user_id: str, amount: Decimal, currency: str):
        """BUSINESS LOGIC: Credit user wallet with deposit amount"""
        wallet = self._wallet_repo.get_by_user(user_id)
        wallet.balance += amount
        wallet.last_updated = datetime.utcnow()
        self._wallet_repo.save(wallet)
```

### Mixed Service Layer (Bad - Infrastructure coupled)

```python
class DepositService:
    """ANTI-PATTERN: Business logic mixed with database/HTTP concerns"""
    
    def process_deposit(self, request: HttpRequest) -> HttpResponse:
        # Infrastructure: HTTP request parsing
        user_id = request.POST.get('user_id')
        amount = Decimal(request.POST.get('amount'))
        
        # Infrastructure: Direct database query
        deposit = Deposit.objects.create(
            user_id=user_id,
            amount=amount,
            status='PENDING'  # Business rule buried in infrastructure
        )
        
        # Business logic coupled to HTTP response
        if amount > 1000:
            return JsonResponse({'status': 'needs_approval'})
        
        # Business logic coupled to database ORM
        Wallet.objects.filter(user_id=user_id).update(
            balance=F('balance') + amount  # Business calculation in query
        )
        
        return JsonResponse({'deposit_id': deposit.id})
```

## 2. Domain Model Pattern

Business logic as methods on domain entities.

### Rich Domain Model (Good - Encapsulated business rules)

```python
@dataclass
class Order:
    """Domain entity with embedded business logic"""
    order_id: str
    items: list[OrderItem]
    status: OrderStatus
    created_at: datetime
    discount_code: Optional[str] = None
    
    def calculate_subtotal(self) -> Decimal:
        """BUSINESS LOGIC: Calculate order subtotal"""
        return sum(item.price * item.quantity for item in self.items)
    
    def calculate_tax(self) -> Decimal:
        """BUSINESS LOGIC: Tax calculation rule"""
        subtotal = self.calculate_subtotal()
        tax_rate = Decimal('0.08')  # Business rule: 8% tax
        return subtotal * tax_rate
    
    def apply_discount(self, discount: Decimal) -> None:
        """BUSINESS LOGIC: Apply discount with validation"""
        if discount > self.calculate_subtotal():
            raise ValueError("Discount cannot exceed subtotal")
        
        if self.status != OrderStatus.PENDING:
            raise InvalidStateError("Can only discount pending orders")
        
        # Business rule applied
        self._discount_amount = discount
    
    def can_be_cancelled(self) -> bool:
        """BUSINESS LOGIC: Cancellation eligibility rule"""
        # Business rule: Only pending/processing orders can be cancelled
        cancellable_statuses = [OrderStatus.PENDING, OrderStatus.PROCESSING]
        
        # Business rule: No cancellation after 24 hours
        hours_since_creation = (datetime.utcnow() - self.created_at).hours
        within_cancellation_window = hours_since_creation <= 24
        
        return self.status in cancellable_statuses and within_cancellation_window
    
    def transition_to_processing(self) -> None:
        """BUSINESS LOGIC: State transition with validation"""
        if self.status != OrderStatus.PENDING:
            raise InvalidStateTransition(
                f"Cannot transition from {self.status} to PROCESSING"
            )
        
        if len(self.items) == 0:
            raise InvalidStateTransition("Cannot process order with no items")
        
        self.status = OrderStatus.PROCESSING
```

### Anemic Domain Model (Anti-pattern - No business logic)

```python
@dataclass
class Order:
    """ANTI-PATTERN: Just a data container, business logic elsewhere"""
    order_id: str
    items: list[OrderItem]
    status: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    
    # No business logic methods - just data
```

## 3. Strategy Pattern for Business Rules

Pluggable business rule implementations.

```python
from abc import ABC, abstractmethod

class PricingStrategy(ABC):
    """BUSINESS LOGIC: Abstract pricing rule"""
    
    @abstractmethod
    def calculate_price(self, base_price: Decimal, customer: Customer) -> Decimal:
        pass

class StandardPricing(PricingStrategy):
    """BUSINESS LOGIC: Standard customer pricing"""
    
    def calculate_price(self, base_price: Decimal, customer: Customer) -> Decimal:
        return base_price

class VIPPricing(PricingStrategy):
    """BUSINESS LOGIC: VIP customer gets 20% discount"""
    
    def calculate_price(self, base_price: Decimal, customer: Customer) -> Decimal:
        return base_price * Decimal('0.80')

class BulkPricing(PricingStrategy):
    """BUSINESS LOGIC: Bulk purchase discount tiers"""
    
    def calculate_price(self, base_price: Decimal, customer: Customer) -> Decimal:
        quantity = customer.current_order_quantity
        
        if quantity >= 100:
            return base_price * Decimal('0.70')  # 30% discount
        elif quantity >= 50:
            return base_price * Decimal('0.85')  # 15% discount
        elif quantity >= 10:
            return base_price * Decimal('0.95')  # 5% discount
        
        return base_price

class PricingService:
    """Uses strategy pattern for flexible pricing rules"""
    
    def __init__(self):
        self._strategies = {
            CustomerTier.STANDARD: StandardPricing(),
            CustomerTier.VIP: VIPPricing(),
            CustomerTier.BULK: BulkPricing(),
        }
    
    def calculate_price(self, product: Product, customer: Customer) -> Decimal:
        """BUSINESS LOGIC: Apply appropriate pricing strategy"""
        strategy = self._strategies[customer.tier]
        return strategy.calculate_price(product.base_price, customer)
```

## 4. Workflow/State Machine Pattern

Multi-step business processes with state transitions.

```python
from enum import Enum
from typing import Callable

class WithdrawalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"

class WithdrawalWorkflow:
    """BUSINESS LOGIC: Withdrawal state machine with business rules"""
    
    # State transition map (business rule: allowed transitions)
    ALLOWED_TRANSITIONS = {
        WithdrawalStatus.PENDING: [WithdrawalStatus.APPROVED, WithdrawalStatus.REJECTED],
        WithdrawalStatus.APPROVED: [WithdrawalStatus.PROCESSING, WithdrawalStatus.REJECTED],
        WithdrawalStatus.PROCESSING: [WithdrawalStatus.COMPLETED, WithdrawalStatus.REJECTED],
        WithdrawalStatus.COMPLETED: [],  # Terminal state
        WithdrawalStatus.REJECTED: [],   # Terminal state
    }
    
    def __init__(self, withdrawal: Withdrawal):
        self.withdrawal = withdrawal
    
    def can_transition_to(self, target_status: WithdrawalStatus) -> bool:
        """BUSINESS LOGIC: Validate state transition"""
        return target_status in self.ALLOWED_TRANSITIONS[self.withdrawal.status]
    
    def approve(self, approver_id: str) -> None:
        """BUSINESS LOGIC: Approve withdrawal with business rules"""
        if not self.can_transition_to(WithdrawalStatus.APPROVED):
            raise InvalidStateTransition("Cannot approve from current state")
        
        # Business rule: Withdrawal amount limits
        if self.withdrawal.amount > Decimal('50000'):
            raise RequiresAdditionalApproval("Amount exceeds single approver limit")
        
        # Business rule: Sufficient balance check
        if self.withdrawal.user.wallet_balance < self.withdrawal.amount:
            raise InsufficientFunds("User wallet balance too low")
        
        self.withdrawal.status = WithdrawalStatus.APPROVED
        self.withdrawal.approved_by = approver_id
        self.withdrawal.approved_at = datetime.utcnow()
    
    def process(self) -> None:
        """BUSINESS LOGIC: Process approved withdrawal"""
        if not self.can_transition_to(WithdrawalStatus.PROCESSING):
            raise InvalidStateTransition("Withdrawal not approved")
        
        # Business rule: Debit wallet before processing
        user = self.withdrawal.user
        user.wallet_balance -= self.withdrawal.amount
        
        self.withdrawal.status = WithdrawalStatus.PROCESSING
        self.withdrawal.processing_started_at = datetime.utcnow()
    
    def complete(self, transaction_id: str) -> None:
        """BUSINESS LOGIC: Complete withdrawal"""
        if not self.can_transition_to(WithdrawalStatus.COMPLETED):
            raise InvalidStateTransition("Withdrawal not in processing state")
        
        self.withdrawal.status = WithdrawalStatus.COMPLETED
        self.withdrawal.completed_at = datetime.utcnow()
        self.withdrawal.external_transaction_id = transaction_id
```

## 5. Repository Pattern

Business logic separation from data access.

```python
from abc import ABC, abstractmethod

class DepositRepository(ABC):
    """Interface defining data access - NO business logic"""
    
    @abstractmethod
    def save(self, deposit: Deposit) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, deposit_id: str) -> Optional[Deposit]:
        pass
    
    @abstractmethod
    def find_pending_for_user(self, user_id: str) -> list[Deposit]:
        pass

class DepositBusinessLogic:
    """BUSINESS LOGIC: Deposit domain logic using repository"""
    
    def __init__(self, deposit_repo: DepositRepository):
        self._repo = deposit_repo
    
    def reconcile_deposits(self, user_id: str) -> ReconciliationResult:
        """BUSINESS LOGIC: Reconciliation rules"""
        pending_deposits = self._repo.find_pending_for_user(user_id)
        
        total_pending = sum(d.amount for d in pending_deposits)
        
        # Business rule: Flag if too many pending deposits
        if len(pending_deposits) > 5:
            return ReconciliationResult(
                status="needs_review",
                reason=f"User has {len(pending_deposits)} pending deposits"
            )
        
        # Business rule: Auto-reconcile small amounts
        if total_pending <= Decimal('100.00'):
            for deposit in pending_deposits:
                deposit.status = DepositStatus.APPROVED
                self._repo.save(deposit)
            
            return ReconciliationResult(status="auto_approved")
        
        return ReconciliationResult(status="manual_review_required")
```

## 6. Decorator-Based Business Logic

Business rules applied via decorators.

```python
from functools import wraps

def requires_kyc_verification(func: Callable) -> Callable:
    """BUSINESS LOGIC: Enforce KYC verification rule"""
    
    @wraps(func)
    def wrapper(self, user_id: str, *args, **kwargs):
        user = self._user_repo.get(user_id)
        
        # Business rule: KYC required for this operation
        if not user.kyc_verified:
            raise KYCRequiredError("User must complete KYC verification")
        
        return func(self, user_id, *args, **kwargs)
    
    return wrapper

def enforces_daily_limit(limit_amount: Decimal):
    """BUSINESS LOGIC: Daily transaction limit rule"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, user_id: str, amount: Decimal, *args, **kwargs):
            today_total = self._transaction_repo.get_daily_total(user_id)
            
            # Business rule: Daily limit enforcement
            if today_total + amount > limit_amount:
                raise DailyLimitExceeded(
                    f"Transaction would exceed daily limit of {limit_amount}"
                )
            
            return func(self, user_id, amount, *args, **kwargs)
        
        return wrapper
    return decorator

class WithdrawalService:
    """Service with decorator-based business rules"""
    
    @requires_kyc_verification
    @enforces_daily_limit(Decimal('10000.00'))
    def create_withdrawal(self, user_id: str, amount: Decimal) -> Withdrawal:
        """BUSINESS LOGIC: Create withdrawal (rules enforced by decorators)"""
        # Core logic here, decorators handle cross-cutting business rules
        withdrawal = Withdrawal(user_id=user_id, amount=amount)
        return withdrawal
```

## 7. Async Business Operations

Asynchronous business logic patterns.

```python
class AsyncDepositProcessor:
    """BUSINESS LOGIC: Asynchronous deposit processing"""
    
    async def process_blockchain_deposit(
        self, 
        transaction_hash: str, 
        confirmations_required: int = 6
    ) -> Deposit:
        """BUSINESS LOGIC: Process blockchain deposit with confirmation rules"""
        
        # Business rule: Wait for required confirmations
        current_confirmations = 0
        while current_confirmations < confirmations_required:
            blockchain_tx = await self._blockchain_client.get_transaction(transaction_hash)
            current_confirmations = blockchain_tx.confirmations
            
            if current_confirmations < confirmations_required:
                await asyncio.sleep(60)  # Poll every minute
        
        # Business rule: Extract deposit details from blockchain
        amount = blockchain_tx.value
        recipient_address = blockchain_tx.to_address
        
        # Business rule: Match to user account
        user = await self._user_repo.find_by_wallet_address(recipient_address)
        if not user:
            raise UnknownRecipientError(f"No user found for address {recipient_address}")
        
        # Create and approve deposit
        deposit = Deposit(
            user_id=user.id,
            amount=amount,
            currency='BTC',
            status=DepositStatus.APPROVED,
            blockchain_tx_hash=transaction_hash,
            confirmations=current_confirmations
        )
        
        await self._deposit_repo.save(deposit)
        return deposit
```

## 8. Validation Rules Pattern

Business validation logic.

```python
from pydantic import BaseModel, validator, root_validator

class TransferRequest(BaseModel):
    """BUSINESS LOGIC: Transfer validation rules"""
    from_user_id: str
    to_user_id: str
    amount: Decimal
    currency: str
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        """BUSINESS RULE: Positive amounts only"""
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('amount')
    def amount_within_limits(cls, v):
        """BUSINESS RULE: Transfer limits"""
        if v > Decimal('100000.00'):
            raise ValueError('Transfer amount exceeds maximum limit')
        if v < Decimal('1.00'):
            raise ValueError('Transfer amount below minimum limit')
        return v
    
    @root_validator
    def cannot_transfer_to_self(cls, values):
        """BUSINESS RULE: No self-transfers"""
        from_user = values.get('from_user_id')
        to_user = values.get('to_user_id')
        
        if from_user == to_user:
            raise ValueError('Cannot transfer to same account')
        
        return values
    
    @validator('currency')
    def supported_currency(cls, v):
        """BUSINESS RULE: Supported currencies"""
        supported = ['USD', 'EUR', 'GBP', 'BTC', 'ETH']
        if v not in supported:
            raise ValueError(f'Currency {v} not supported')
        return v
```

## Pattern Recognition Tips

**Identifying Service Layer**:
- Class names ending in `Service`, `Manager`, `Handler`, `Processor`
- Methods orchestrating multiple operations
- Dependency injection of repositories/clients

**Identifying Domain Logic**:
- Rich model methods (beyond getters/setters)
- Business rule validation in entity methods
- State transition methods
- Calculation methods

**Identifying Infrastructure**:
- HTTP request/response handling
- Database query construction
- API client calls
- Serialization/deserialization
- Framework decorators (`@app.route`, `@api_view`)

**Red Flags for Coupling**:
- Business calculations in view/controller functions
- Domain logic in database queries
- Business rules in serializers
- State transitions in API handlers