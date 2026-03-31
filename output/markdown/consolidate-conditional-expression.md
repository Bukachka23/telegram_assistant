# Consolidate Conditional Expression

**URL:** https://refactoring.guru/consolidate-conditional-expression
**Type:** technique  |  **Category:** Simplifying Conditional Expressions


## Consolidate Conditional Expression

Problem You have multiple conditionals that lead to the same result or action. Solution Consolidate all these conditionals in a single expression. Before double disabilityAmount() {
  if (seniority < 2) {
    return 0;
  }
  if (monthsDisabled > 12) {
    return 0;
  }
  if (isPartTime) {
    return 0;
  }
  // Compute the disability amount.
  // ...
} After double disabilityAmount() {
  if (isNotEligibleForDisability()) {
    return 0;
  }
  // Compute the disability amount.
  // ...
} Before double DisabilityAmount() 
{
  if (seniority < 2) 
  {
    return 0;
  }
  if (monthsDisabled > 12) 
  {
    return 0;
  }
  if (isPartTime) 
  {
    return 0;
  }
  // Compute the disability amount.
  // ...
} After double DisabilityAmount()
{
  if (IsNotEligibleForDisability())
  {
    return 0;
  }
  // Compute the disability amount.
  // ...
} Before function disabilityAmount() {
  if ($this->seniority < 2) {
    return 0;
  }
  if ($this->monthsDisabled > 12) {
    return 0;
  }
  if ($this->isPartTime) {
    return 0;
  }
  // compute the disability amount
  ... After function disabilityAmount() {
  if ($this->isNotEligibleForDisability()) {
    return 0;
  }
  // compute the disability amount
  ... Before def disabilityAmount():
    if seniority < 2:
        return 0
    if monthsDisabled > 12:
        return 0
    if isPartTime:
        return 0
    # Compute the disability amount.
    # ... After def disabilityAmount():
    if isNotEligibleForDisability():
        return 0
    # Compute the disability amount.
    # ... Before disabilityAmount(): number {
  if (seniority < 2) {
    return 0;
  }
  if (monthsDisabled > 12) {
    return 0;
  }
  if (isPartTime) {
    return 0;
  }
  // Compute the disability amount.
  // ...
} After disabilityAmount(): number {
  if (isNotEligibleForDisability()) {
    return 0;
  }
  // Compute the disability amount.
  // ...
}


## Why Refactor

Your code contains many alternating operators that perform identical actions. It isn’t clear why the operators are split up. The main purpose of consolidation is to extract the conditional to a separate method for greater clarity.


## Benefits

Eliminates duplicate control flow code. Combining multiple conditionals that have the same “destination” helps to show that you’re doing only one complicated check leading to one action. By consolidating all operators, you can now isolate this complex expression in a new method with a name that explains the conditional’s purpose.


## How to Refactor

Before refactoring, make sure that the conditionals don’t have any “side effects” or otherwise modify something, instead of simply returning values. Side effects may be hiding in the code executed inside the operator itself, such as when something is added to a variable based on the results of a conditional. Consolidate the conditionals in a single expression by using and and or . As a general rule when consolidating: Nested conditionals are joined using and . Consecutive conditionals are joined with or . Perform Extract Method on the operator conditions and give the method a name that reflects the expression’s purpose.


## Code Examples

### unknown

**Before**
```unknown
double disabilityAmount() {
  if (seniority < 2) {
    return 0;
  }
  if (monthsDisabled > 12) {
    return 0;
  }
  if (isPartTime) {
    return 0;
  }
  // Compute the disability amount.
  // ...
}
```

**After**
```unknown
double disabilityAmount() {
  if (isNotEligibleForDisability()) {
    return 0;
  }
  // Compute the disability amount.
  // ...
}
```

### unknown

**Before**
```unknown
double DisabilityAmount() 
{
  if (seniority < 2) 
  {
    return 0;
  }
  if (monthsDisabled > 12) 
  {
    return 0;
  }
  if (isPartTime) 
  {
    return 0;
  }
  // Compute the disability amount.
  // ...
}
```

**After**
```unknown
double DisabilityAmount()
{
  if (IsNotEligibleForDisability())
  {
    return 0;
  }
  // Compute the disability amount.
  // ...
}
```

### unknown

**Before**
```unknown
function disabilityAmount() {
  if ($this->seniority < 2) {
    return 0;
  }
  if ($this->monthsDisabled > 12) {
    return 0;
  }
  if ($this->isPartTime) {
    return 0;
  }
  // compute the disability amount
  ...
```

**After**
```unknown
function disabilityAmount() {
  if ($this->isNotEligibleForDisability()) {
    return 0;
  }
  // compute the disability amount
  ...
```

### unknown

**Before**
```unknown
def disabilityAmount():
    if seniority < 2:
        return 0
    if monthsDisabled > 12:
        return 0
    if isPartTime:
        return 0
    # Compute the disability amount.
    # ...
```

**After**
```unknown
def disabilityAmount():
    if isNotEligibleForDisability():
        return 0
    # Compute the disability amount.
    # ...
```

### unknown

**Before**
```unknown
disabilityAmount(): number {
  if (seniority < 2) {
    return 0;
  }
  if (monthsDisabled > 12) {
    return 0;
  }
  if (isPartTime) {
    return 0;
  }
  // Compute the disability amount.
  // ...
}
```

**After**
```unknown
disabilityAmount(): number {
  if (isNotEligibleForDisability()) {
    return 0;
  }
  // Compute the disability amount.
  // ...
}
```
