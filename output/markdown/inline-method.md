# Inline Method

**URL:** https://refactoring.guru/inline-method
**Type:** technique  |  **Category:** Composing Methods


## Inline Method

Problem When a method body is more obvious than the method itself, use this technique. Solution Replace calls to the method with the method’s content and delete the method itself. Before class PizzaDelivery {
  // ...
  int getRating() {
    return moreThanFiveLateDeliveries() ? 2 : 1;
  }
  boolean moreThanFiveLateDeliveries() {
    return numberOfLateDeliveries > 5;
  }
} After class PizzaDelivery {
  // ...
  int getRating() {
    return numberOfLateDeliveries > 5 ? 2 : 1;
  }
} Before class PizzaDelivery 
{
  // ...
  int GetRating() 
  {
    return MoreThanFiveLateDeliveries() ? 2 : 1;
  }
  bool MoreThanFiveLateDeliveries() 
  {
    return numberOfLateDeliveries > 5;
  }
} After class PizzaDelivery 
{
  // ...
  int GetRating() 
  {
    return numberOfLateDeliveries > 5 ? 2 : 1;
  }
} Before function getRating() {
  return ($this->moreThanFiveLateDeliveries()) ? 2 : 1;
}
function moreThanFiveLateDeliveries() {
  return $this->numberOfLateDeliveries > 5;
} After function getRating() {
  return ($this->numberOfLateDeliveries > 5) ? 2 : 1;
} Before class PizzaDelivery:
    # ...
    def getRating(self):
        return 2 if self.moreThanFiveLateDeliveries() else 1
  
    def moreThanFiveLateDeliveries(self):
        return self.numberOfLateDeliveries > 5 After class PizzaDelivery:
  # ...
  def getRating(self):
    return 2 if self.numberOfLateDeliveries > 5 else 1 Before class PizzaDelivery {
  // ...
  getRating(): number {
    return moreThanFiveLateDeliveries() ? 2 : 1;
  }
  moreThanFiveLateDeliveries(): boolean {
    return numberOfLateDeliveries > 5;
  }
} After class PizzaDelivery {
  // ...
  getRating(): number {
    return numberOfLateDeliveries > 5 ? 2 : 1;
  }
}


## Why Refactor

A method simply delegates to another method. In itself, this delegation is no problem. But when there are many such methods, they become a confusing tangle that’s hard to sort through. Often methods aren’t too short originally , but become that way as changes are made to the program. So don’t be shy about getting rid of methods that have outlived their use.


## Benefits

By minimizing the number of unneeded methods, you make the code more straightforward.


## How to Refactor

Make sure that the method isn’t redefined in subclasses. If the method is redefined, refrain from this technique. Find all calls to the method. Replace these calls with the content of the method. Delete the method.


## Code Examples

### unknown

**Before**
```unknown
class PizzaDelivery {
  // ...
  int getRating() {
    return moreThanFiveLateDeliveries() ? 2 : 1;
  }
  boolean moreThanFiveLateDeliveries() {
    return numberOfLateDeliveries > 5;
  }
}
```

**After**
```unknown
class PizzaDelivery {
  // ...
  int getRating() {
    return numberOfLateDeliveries > 5 ? 2 : 1;
  }
}
```

### unknown

**Before**
```unknown
class PizzaDelivery 
{
  // ...
  int GetRating() 
  {
    return MoreThanFiveLateDeliveries() ? 2 : 1;
  }
  bool MoreThanFiveLateDeliveries() 
  {
    return numberOfLateDeliveries > 5;
  }
}
```

**After**
```unknown
class PizzaDelivery 
{
  // ...
  int GetRating() 
  {
    return numberOfLateDeliveries > 5 ? 2 : 1;
  }
}
```

### unknown

**Before**
```unknown
function getRating() {
  return ($this->moreThanFiveLateDeliveries()) ? 2 : 1;
}
function moreThanFiveLateDeliveries() {
  return $this->numberOfLateDeliveries > 5;
}
```

**After**
```unknown
function getRating() {
  return ($this->numberOfLateDeliveries > 5) ? 2 : 1;
}
```

### unknown

**Before**
```unknown
class PizzaDelivery:
    # ...
    def getRating(self):
        return 2 if self.moreThanFiveLateDeliveries() else 1
  
    def moreThanFiveLateDeliveries(self):
        return self.numberOfLateDeliveries > 5
```

**After**
```unknown
class PizzaDelivery:
  # ...
  def getRating(self):
    return 2 if self.numberOfLateDeliveries > 5 else 1
```

### unknown

**Before**
```unknown
class PizzaDelivery {
  // ...
  getRating(): number {
    return moreThanFiveLateDeliveries() ? 2 : 1;
  }
  moreThanFiveLateDeliveries(): boolean {
    return numberOfLateDeliveries > 5;
  }
}
```

**After**
```unknown
class PizzaDelivery {
  // ...
  getRating(): number {
    return numberOfLateDeliveries > 5 ? 2 : 1;
  }
}
```
