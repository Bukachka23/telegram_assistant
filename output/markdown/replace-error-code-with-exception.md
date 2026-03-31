# Replace Error Code with Exception

**URL:** https://refactoring.guru/replace-error-code-with-exception
**Type:** technique  |  **Category:** Simplifying Method Calls


## Replace Error Code with Exception

Problem A method returns a special value that indicates an error? Solution Throw an exception instead. Before int withdraw(int amount) {
  if (amount > _balance) {
    return -1;
  }
  else {
    balance -= amount;
    return 0;
  }
} After void withdraw(int amount) throws BalanceException {
  if (amount > _balance) {
    throw new BalanceException();
  }
  balance -= amount;
} Before int Withdraw(int amount) 
{
  if (amount > _balance) 
  {
    return -1;
  }
  else 
  {
    balance -= amount;
    return 0;
  }
} After ///<exception cref="BalanceException">Thrown when amount > _balance</exception>
void Withdraw(int amount)
{
  if (amount > _balance) 
  {
    throw new BalanceException();
  }
  balance -= amount;
} Before function withdraw($amount) {
  if ($amount > $this->balance) {
    return -1;
  } else {
    $this->balance -= $amount;
    return 0;
  }
} After function withdraw($amount) {
  if ($amount > $this->balance) {
    throw new BalanceException;
  }
  $this->balance -= $amount;
} Before def withdraw(self, amount):
    if amount > self.balance:
        return -1
    else:
        self.balance -= amount
    return 0 After def withdraw(self, amount):
    if amount > self.balance:
        raise BalanceException()
    self.balance -= amount Before withdraw(amount: number): number {
  if (amount > _balance) {
    return -1;
  }
  else {
    balance -= amount;
    return 0;
  }
} After withdraw(amount: number): void {
  if (amount > _balance) {
    throw new Error();
  }
  balance -= amount;
}


## Why Refactor

Returning error codes is an obsolete holdover from procedural programming. In modern programming, error handling is performed by special classes, which are named exceptions. If a problem occurs, you “throw” an error, which is then “caught” by one of the exception handlers. Special error-handling code, which is ignored in normal conditions, is activated to respond.


## Benefits

Frees code from a large number of conditionals for checking various error codes. Exception handlers are a much more succinct way to differentiate normal execution paths from abnormal ones. Exception classes can implement their own methods, thus containing part of the error handling functionality (such as for sending error messages). Unlike exceptions, error codes can’t be used in a constructor, since a constructor must return only a new object.


## Drawbacks

An exception handler can turn into a goto-like crutch. Avoid this! Don’t use exceptions to manage code execution. Exceptions should be thrown only to inform of an error or critical situation.


## How to Refactor

Try to perform these refactoring steps for only one error code at a time. This will make it easier to keep all the important information in your head and avoid errors. Find all calls to a method that returns error codes and, instead of checking for an error code, wrap it in try / catch blocks. Inside the method, instead of returning an error code, throw an exception. Change the method signature so that it contains information about the exception being thrown ( @throws section).


## Code Examples

### unknown

**Before**
```unknown
int withdraw(int amount) {
  if (amount > _balance) {
    return -1;
  }
  else {
    balance -= amount;
    return 0;
  }
}
```

**After**
```unknown
void withdraw(int amount) throws BalanceException {
  if (amount > _balance) {
    throw new BalanceException();
  }
  balance -= amount;
}
```

### unknown

**Before**
```unknown
int Withdraw(int amount) 
{
  if (amount > _balance) 
  {
    return -1;
  }
  else 
  {
    balance -= amount;
    return 0;
  }
}
```

**After**
```unknown
///<exception cref="BalanceException">Thrown when amount > _balance</exception>
void Withdraw(int amount)
{
  if (amount > _balance) 
  {
    throw new BalanceException();
  }
  balance -= amount;
}
```

### unknown

**Before**
```unknown
function withdraw($amount) {
  if ($amount > $this->balance) {
    return -1;
  } else {
    $this->balance -= $amount;
    return 0;
  }
}
```

**After**
```unknown
function withdraw($amount) {
  if ($amount > $this->balance) {
    throw new BalanceException;
  }
  $this->balance -= $amount;
}
```

### unknown

**Before**
```unknown
def withdraw(self, amount):
    if amount > self.balance:
        return -1
    else:
        self.balance -= amount
    return 0
```

**After**
```unknown
def withdraw(self, amount):
    if amount > self.balance:
        raise BalanceException()
    self.balance -= amount
```

### unknown

**Before**
```unknown
withdraw(amount: number): number {
  if (amount > _balance) {
    return -1;
  }
  else {
    balance -= amount;
    return 0;
  }
}
```

**After**
```unknown
withdraw(amount: number): void {
  if (amount > _balance) {
    throw new Error();
  }
  balance -= amount;
}
```
