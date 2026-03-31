# Replace Method with Method Object

**URL:** https://refactoring.guru/replace-method-with-method-object
**Type:** technique  |  **Category:** Composing Methods


## Replace Method with Method Object

Problem You have a long method in which the local variables are so intertwined that you can’t apply Extract Method . Solution Transform the method into a separate class so that the local variables become fields of the class. Then you can split the method into several methods within the same class. Before class Order {
  // ...
  public double price() {
    double primaryBasePrice;
    double secondaryBasePrice;
    double tertiaryBasePrice;
    // Perform long computation.
  }
} After class Order {
  // ...
  public double price() {
    return new PriceCalculator(this).compute();
  }
}

class PriceCalculator {
  private double primaryBasePrice;
  private double secondaryBasePrice;
  private double tertiaryBasePrice;
  
  public PriceCalculator(Order order) {
    // Copy relevant information from the
    // order object.
  }
  
  public double compute() {
    // Perform long computation.
  }
} Before public class Order 
{
  // ...
  public double Price() 
  {
    double primaryBasePrice;
    double secondaryBasePrice;
    double tertiaryBasePrice;
    // Perform long computation.
  }
} After public class Order 
{
  // ...
  public double Price() 
  {
    return new PriceCalculator(this).Compute();
  }
}

public class PriceCalculator 
{
  private double primaryBasePrice;
  private double secondaryBasePrice;
  private double tertiaryBasePrice;
  
  public PriceCalculator(Order order) 
  {
    // Copy relevant information from the
    // order object.
  }
  
  public double Compute() 
  {
    // Perform long computation.
  }
} Before class Order {
  // ...
  public function price() {
    $primaryBasePrice = 10;
    $secondaryBasePrice = 20;
    $tertiaryBasePrice = 30;
    // Perform long computation.
  }
} After class Order {
  // ...
  public function price() {
    return (new PriceCalculator($this))->compute();
  }
}

class PriceCalculator {
  private $primaryBasePrice;
  private $secondaryBasePrice;
  private $tertiaryBasePrice;
  
  public function __construct(Order $order) {
      // Copy relevant information from the
      // order object.
  }
  
  public function compute() {
    // Perform long computation.
  }
} Before class Order:
    # ...
    def price(self):
        primaryBasePrice = 0
        secondaryBasePrice = 0
        tertiaryBasePrice = 0
        # Perform long computation. After class Order:
    # ...
    def price(self):
        return PriceCalculator(self).compute()


class PriceCalculator:
    def __init__(self, order):
        self._primaryBasePrice = 0
        self._secondaryBasePrice = 0
        self._tertiaryBasePrice = 0
        # Copy relevant information from the
        # order object.

    def compute(self):
        # Perform long computation. Before class Order {
  // ...
  price(): number {
    let primaryBasePrice;
    let secondaryBasePrice;
    let tertiaryBasePrice;
    // Perform long computation.
  }
} After class Order {
  // ...
  price(): number {
    return new PriceCalculator(this).compute();
  }
}

class PriceCalculator {
  private _primaryBasePrice: number;
  private _secondaryBasePrice: number;
  private _tertiaryBasePrice: number;
  
  constructor(order: Order) {
    // Copy relevant information from the
    // order object.
  }
  
  compute(): number {
    // Perform long computation.
  }
}


## Why Refactor

A method is too long and you can’t separate it due to tangled masses of local variables that are hard to isolate from each other. The first step is to isolate the entire method into a separate class and turn its local variables into fields of the class. Firstly, this allows isolating the problem at the class level. Secondly, it paves the way for splitting a large and unwieldy method into smaller ones that wouldn’t fit with the purpose of the original class anyway.


## Benefits

Isolating a long method in its own class allows stopping a method from ballooning in size. This also allows splitting it into submethods within the class, without polluting the original class with utility methods.


## Drawbacks

Another class is added, increasing the overall complexity of the program.


## How to Refactor

Create a new class. Name it based on the purpose of the method that you’re refactoring. In the new class, create a private field for storing a reference to an instance of the class in which the method was previously located. It could be used to get some required data from the original class if needed. Create a separate private field for each local variable of the method. Create a constructor that accepts as parameters the values of all local variables of the method and also initializes the corresponding private fields. Declare the main method and copy the code of the original method to it, replacing the local variables with private fields. Replace the body of the original method in the original class by creating a method object and calling its main method.


## Code Examples

### unknown

**Before**
```unknown
class Order {
  // ...
  public double price() {
    double primaryBasePrice;
    double secondaryBasePrice;
    double tertiaryBasePrice;
    // Perform long computation.
  }
}
```

**After**
```unknown
class Order {
  // ...
  public double price() {
    return new PriceCalculator(this).compute();
  }
}

class PriceCalculator {
  private double primaryBasePrice;
  private double secondaryBasePrice;
  private double tertiaryBasePrice;
  
  public PriceCalculator(Order order) {
    // Copy relevant information from the
    // order object.
  }
  
  public double compute() {
    // Perform long computation.
  }
}
```

### unknown

**Before**
```unknown
public class Order 
{
  // ...
  public double Price() 
  {
    double primaryBasePrice;
    double secondaryBasePrice;
    double tertiaryBasePrice;
    // Perform long computation.
  }
}
```

**After**
```unknown
public class Order 
{
  // ...
  public double Price() 
  {
    return new PriceCalculator(this).Compute();
  }
}

public class PriceCalculator 
{
  private double primaryBasePrice;
  private double secondaryBasePrice;
  private double tertiaryBasePrice;
  
  public PriceCalculator(Order order) 
  {
    // Copy relevant information from the
    // order object.
  }
  
  public double Compute() 
  {
    // Perform long computation.
  }
}
```

### unknown

**Before**
```unknown
class Order {
  // ...
  public function price() {
    $primaryBasePrice = 10;
    $secondaryBasePrice = 20;
    $tertiaryBasePrice = 30;
    // Perform long computation.
  }
}
```

**After**
```unknown
class Order {
  // ...
  public function price() {
    return (new PriceCalculator($this))->compute();
  }
}

class PriceCalculator {
  private $primaryBasePrice;
  private $secondaryBasePrice;
  private $tertiaryBasePrice;
  
  public function __construct(Order $order) {
      // Copy relevant information from the
      // order object.
  }
  
  public function compute() {
    // Perform long computation.
  }
}
```

### unknown

**Before**
```unknown
class Order:
    # ...
    def price(self):
        primaryBasePrice = 0
        secondaryBasePrice = 0
        tertiaryBasePrice = 0
        # Perform long computation.
```

**After**
```unknown
class Order:
    # ...
    def price(self):
        return PriceCalculator(self).compute()


class PriceCalculator:
    def __init__(self, order):
        self._primaryBasePrice = 0
        self._secondaryBasePrice = 0
        self._tertiaryBasePrice = 0
        # Copy relevant information from the
        # order object.

    def compute(self):
        # Perform long computation.
```

### unknown

**Before**
```unknown
class Order {
  // ...
  price(): number {
    let primaryBasePrice;
    let secondaryBasePrice;
    let tertiaryBasePrice;
    // Perform long computation.
  }
}
```

**After**
```unknown
class Order {
  // ...
  price(): number {
    return new PriceCalculator(this).compute();
  }
}

class PriceCalculator {
  private _primaryBasePrice: number;
  private _secondaryBasePrice: number;
  private _tertiaryBasePrice: number;
  
  constructor(order: Order) {
    // Copy relevant information from the
    // order object.
  }
  
  compute(): number {
    // Perform long computation.
  }
}
```
