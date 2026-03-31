# Consolidate Duplicate Conditional Fragments

**URL:** https://refactoring.guru/consolidate-duplicate-conditional-fragments
**Type:** technique  |  **Category:** Simplifying Conditional Expressions


## Consolidate Duplicate Conditional Fragments

Problem Identical code can be found in all branches of a conditional. Solution Move the code outside of the conditional. Before if (isSpecialDeal()) {
  total = price * 0.95;
  send();
}
else {
  total = price * 0.98;
  send();
} After if (isSpecialDeal()) {
  total = price * 0.95;
}
else {
  total = price * 0.98;
}
send(); Before if (IsSpecialDeal()) 
{
  total = price * 0.95;
  Send();
}
else 
{
  total = price * 0.98;
  Send();
} After if (IsSpecialDeal())
{
  total = price * 0.95;
}
else
{
  total = price * 0.98;
}
Send(); Before if (isSpecialDeal()) {
  $total = $price * 0.95;
  send();
} else {
  $total = $price * 0.98;
  send();
} After if (isSpecialDeal()) {
  $total = $price * 0.95;
} else {
  $total = $price * 0.98;
}
send(); Before if isSpecialDeal():
    total = price * 0.95
    send()
else:
    total = price * 0.98
    send() After if isSpecialDeal():
    total = price * 0.95
else:
    total = price * 0.98
send() Before if (isSpecialDeal()) {
  total = price * 0.95;
  send();
}
else {
  total = price * 0.98;
  send();
} After if (isSpecialDeal()) {
  total = price * 0.95;
}
else {
  total = price * 0.98;
}
send();


## Why Refactor

Duplicate code is found inside all branches of a conditional, often as the result of evolution of the code within the conditional branches. Team development can be a contributing factor to this.


## Benefits

Code deduplication.


## How to Refactor

If the duplicated code is at the beginning of the conditional branches, move the code to a place before the conditional. If the code is executed at the end of the branches, place it after the conditional. If the duplicate code is randomly situated inside the branches, first try to move the code to the beginning or end of the branch, depending on whether it changes the result of the subsequent code. If appropriate and the duplicate code is longer than one line, try using Extract Method .


## Code Examples

### unknown

**Before**
```unknown
if (isSpecialDeal()) {
  total = price * 0.95;
  send();
}
else {
  total = price * 0.98;
  send();
}
```

**After**
```unknown
if (isSpecialDeal()) {
  total = price * 0.95;
}
else {
  total = price * 0.98;
}
send();
```

### unknown

**Before**
```unknown
if (IsSpecialDeal()) 
{
  total = price * 0.95;
  Send();
}
else 
{
  total = price * 0.98;
  Send();
}
```

**After**
```unknown
if (IsSpecialDeal())
{
  total = price * 0.95;
}
else
{
  total = price * 0.98;
}
Send();
```

### unknown

**Before**
```unknown
if (isSpecialDeal()) {
  $total = $price * 0.95;
  send();
} else {
  $total = $price * 0.98;
  send();
}
```

**After**
```unknown
if (isSpecialDeal()) {
  $total = $price * 0.95;
} else {
  $total = $price * 0.98;
}
send();
```

### unknown

**Before**
```unknown
if isSpecialDeal():
    total = price * 0.95
    send()
else:
    total = price * 0.98
    send()
```

**After**
```unknown
if isSpecialDeal():
    total = price * 0.95
else:
    total = price * 0.98
send()
```

### unknown

**Before**
```unknown
if (isSpecialDeal()) {
  total = price * 0.95;
  send();
}
else {
  total = price * 0.98;
  send();
}
```

**After**
```unknown
if (isSpecialDeal()) {
  total = price * 0.95;
}
else {
  total = price * 0.98;
}
send();
```
