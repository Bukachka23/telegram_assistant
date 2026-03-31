# Replace Temp with Query

**URL:** https://refactoring.guru/replace-temp-with-query
**Type:** technique  |  **Category:** Composing Methods


## Replace Temp with Query

Problem You place the result of an expression in a local variable for later use in your code. Solution Move the entire expression to a separate method and return the result from it. Query the method instead of using a variable. Incorporate the new method in other methods, if necessary. Before double calculateTotal() {
  double basePrice = quantity * itemPrice;
  if (basePrice > 1000) {
    return basePrice * 0.95;
  }
  else {
    return basePrice * 0.98;
  }
} After double calculateTotal() {
  if (basePrice() > 1000) {
    return basePrice() * 0.95;
  }
  else {
    return basePrice() * 0.98;
  }
}
double basePrice() {
  return quantity * itemPrice;
} Before double CalculateTotal() 
{
  double basePrice = quantity * itemPrice;
  
  if (basePrice > 1000) 
  {
    return basePrice * 0.95;
  }
  else 
  {
    return basePrice * 0.98;
  }
} After double CalculateTotal() 
{
  if (BasePrice() > 1000) 
  {
    return BasePrice() * 0.95;
  }
  else 
  {
    return BasePrice() * 0.98;
  }
}
double BasePrice() 
{
  return quantity * itemPrice;
} Before $basePrice = $this->quantity * $this->itemPrice;
if ($basePrice > 1000) {
  return $basePrice * 0.95;
} else {
  return $basePrice * 0.98;
} After if ($this->basePrice() > 1000) {
  return $this->basePrice() * 0.95;
} else {
  return $this->basePrice() * 0.98;
}

...

function basePrice() {
  return $this->quantity * $this->itemPrice;
} Before def calculateTotal():
    basePrice = quantity * itemPrice
    if basePrice > 1000:
        return basePrice * 0.95
    else:
        return basePrice * 0.98 After def calculateTotal():
    if basePrice() > 1000:
        return basePrice() * 0.95
    else:
        return basePrice() * 0.98

def basePrice():
    return quantity * itemPrice Before calculateTotal(): number {
  let basePrice = quantity * itemPrice;
  if (basePrice > 1000) {
    return basePrice * 0.95;
  }
  else {
    return basePrice * 0.98;
  }
} After calculateTotal(): number {
  if (basePrice() > 1000) {
    return basePrice() * 0.95;
  }
  else {
    return basePrice() * 0.98;
  }
}
basePrice(): number {
  return quantity * itemPrice;
}


## Why Refactor

This refactoring can lay the groundwork for applying Extract Method for a portion of a very long method. The same expression may sometimes be found in other methods as well, which is one reason to consider creating a common method.


## Benefits

Code readability. It’s much easier to understand the purpose of the method getTax() than the line orderPrice() * 0.2 . Slimmer code via deduplication, if the line being replaced is used in multiple methods.


## Performance

This refactoring may prompt the question of whether this approach is liable to cause a performance hit. The honest answer is: yes, it is, since the resulting code may be burdened by querying a new method. But with today’s fast CPUs and excellent compilers, the burden will almost always be minimal. By contrast, readable code and the ability to reuse this method in other places in program code—thanks to this refactoring approach—are very noticeable benefits. Nonetheless, if your temp variable is used to cache the result of a truly time-consuming expression, you may want to stop this refactoring after extracting the expression to a new method.


## How to Refactor

Make sure that a value is assigned to the variable once and only once within the method. If not, use Split Temporary Variable to ensure that the variable will be used only to store the result of your expression. Use Extract Method to place the expression of interest in a new method. Make sure that this method only returns a value and doesn’t change the state of the object. If the method affects the visible state of the object, use Separate Query from Modifier . Replace the variable with a query to your new method.


## Code Examples

### unknown

**Before**
```unknown
double calculateTotal() {
  double basePrice = quantity * itemPrice;
  if (basePrice > 1000) {
    return basePrice * 0.95;
  }
  else {
    return basePrice * 0.98;
  }
}
```

**After**
```unknown
double calculateTotal() {
  if (basePrice() > 1000) {
    return basePrice() * 0.95;
  }
  else {
    return basePrice() * 0.98;
  }
}
double basePrice() {
  return quantity * itemPrice;
}
```

### unknown

**Before**
```unknown
double CalculateTotal() 
{
  double basePrice = quantity * itemPrice;
  
  if (basePrice > 1000) 
  {
    return basePrice * 0.95;
  }
  else 
  {
    return basePrice * 0.98;
  }
}
```

**After**
```unknown
double CalculateTotal() 
{
  if (BasePrice() > 1000) 
  {
    return BasePrice() * 0.95;
  }
  else 
  {
    return BasePrice() * 0.98;
  }
}
double BasePrice() 
{
  return quantity * itemPrice;
}
```

### unknown

**Before**
```unknown
$basePrice = $this->quantity * $this->itemPrice;
if ($basePrice > 1000) {
  return $basePrice * 0.95;
} else {
  return $basePrice * 0.98;
}
```

**After**
```unknown
if ($this->basePrice() > 1000) {
  return $this->basePrice() * 0.95;
} else {
  return $this->basePrice() * 0.98;
}

...

function basePrice() {
  return $this->quantity * $this->itemPrice;
}
```

### unknown

**Before**
```unknown
def calculateTotal():
    basePrice = quantity * itemPrice
    if basePrice > 1000:
        return basePrice * 0.95
    else:
        return basePrice * 0.98
```

**After**
```unknown
def calculateTotal():
    if basePrice() > 1000:
        return basePrice() * 0.95
    else:
        return basePrice() * 0.98

def basePrice():
    return quantity * itemPrice
```

### unknown

**Before**
```unknown
calculateTotal(): number {
  let basePrice = quantity * itemPrice;
  if (basePrice > 1000) {
    return basePrice * 0.95;
  }
  else {
    return basePrice * 0.98;
  }
}
```

**After**
```unknown
calculateTotal(): number {
  if (basePrice() > 1000) {
    return basePrice() * 0.95;
  }
  else {
    return basePrice() * 0.98;
  }
}
basePrice(): number {
  return quantity * itemPrice;
}
```
