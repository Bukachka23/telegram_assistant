# Introduce Null Object

**URL:** https://refactoring.guru/introduce-null-object
**Type:** technique  |  **Category:** Simplifying Conditional Expressions


## Introduce Null Object

Problem Since some methods return null instead of real objects, you have many checks for null in your code. Solution Instead of null , return a null object that exhibits the default behavior. Before if (customer == null) {
  plan = BillingPlan.basic();
}
else {
  plan = customer.getPlan();
} After class NullCustomer extends Customer {
  boolean isNull() {
    return true;
  }
  Plan getPlan() {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
customer = (order.customer != null) ?
  order.customer : new NullCustomer();

// Use Null-object as if it's normal subclass.
plan = customer.getPlan(); Before if (customer == null) 
{
  plan = BillingPlan.Basic();
}
else 
{
  plan = customer.GetPlan();
} After public sealed class NullCustomer: Customer 
{
  public override bool IsNull 
  {
    get { return true; }
  }
  
  public override Plan GetPlan() 
  {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
customer = order.customer ?? new NullCustomer();

// Use Null-object as if it's normal subclass.
plan = customer.GetPlan(); Before if ($customer === null) {
  $plan = BillingPlan::basic();
} else {
  $plan = $customer->getPlan();
} After class NullCustomer extends Customer {
  public function isNull() {
    return true;
  }
  public function getPlan() {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
$customer = ($order->customer !== null) ?
  $order->customer :
  new NullCustomer;

// Use Null-object as if it's normal subclass.
$plan = $customer->getPlan(); Before if customer is None:
    plan = BillingPlan.basic()
else:
    plan = customer.getPlan() After class NullCustomer(Customer):

    def isNull(self):
        return True

    def getPlan(self):
        return self.NullPlan()

    # Some other NULL functionality.

# Replace null values with Null-object.
customer = order.customer or NullCustomer()

# Use Null-object as if it's normal subclass.
plan = customer.getPlan() Before if (customer == null) {
  plan = BillingPlan.basic();
}
else {
  plan = customer.getPlan();
} After class NullCustomer extends Customer {
  isNull(): boolean {
    return true;
  }
  getPlan(): Plan {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
let customer = (order.customer != null) ?
  order.customer : new NullCustomer();

// Use Null-object as if it's normal subclass.
plan = customer.getPlan();


## Why Refactor

Dozens of checks for null make your code longer and uglier.


## Drawbacks

The price of getting rid of conditionals is creating yet another new class.


## How to Refactor

From the class in question, create a subclass that will perform the role of null object. In both classes, create the method isNull() , which will return true for a null object and false for a real class. Find all places where the code may return null instead of a real object. Change the code so that it returns a null object. Find all places where the variables of the real class are compared with null . Replace these checks with a call for isNull() . If methods of the original class are run in these conditionals when a value doesn’t equal null , redefine these methods in the null class and insert the code from the else part of the condition there. Then you can delete the entire conditional and differing behavior will be implemented via polymorphism. If things aren’t so simple and the methods can’t be redefined, see if you can simply extract the operators that were supposed to be performed in the case of a null value to new methods of the null object. Call these methods instead of the old code in else as the operations by default.


## Code Examples

### unknown

**Before**
```unknown
if (customer == null) {
  plan = BillingPlan.basic();
}
else {
  plan = customer.getPlan();
}
```

**After**
```unknown
class NullCustomer extends Customer {
  boolean isNull() {
    return true;
  }
  Plan getPlan() {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
customer = (order.customer != null) ?
  order.customer : new NullCustomer();

// Use Null-object as if it's normal subclass.
plan = customer.getPlan();
```

### unknown

**Before**
```unknown
if (customer == null) 
{
  plan = BillingPlan.Basic();
}
else 
{
  plan = customer.GetPlan();
}
```

**After**
```unknown
public sealed class NullCustomer: Customer 
{
  public override bool IsNull 
  {
    get { return true; }
  }
  
  public override Plan GetPlan() 
  {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
customer = order.customer ?? new NullCustomer();

// Use Null-object as if it's normal subclass.
plan = customer.GetPlan();
```

### unknown

**Before**
```unknown
if ($customer === null) {
  $plan = BillingPlan::basic();
} else {
  $plan = $customer->getPlan();
}
```

**After**
```unknown
class NullCustomer extends Customer {
  public function isNull() {
    return true;
  }
  public function getPlan() {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
$customer = ($order->customer !== null) ?
  $order->customer :
  new NullCustomer;

// Use Null-object as if it's normal subclass.
$plan = $customer->getPlan();
```

### unknown

**Before**
```unknown
if customer is None:
    plan = BillingPlan.basic()
else:
    plan = customer.getPlan()
```

**After**
```unknown
class NullCustomer(Customer):

    def isNull(self):
        return True

    def getPlan(self):
        return self.NullPlan()

    # Some other NULL functionality.

# Replace null values with Null-object.
customer = order.customer or NullCustomer()

# Use Null-object as if it's normal subclass.
plan = customer.getPlan()
```

### unknown

**Before**
```unknown
if (customer == null) {
  plan = BillingPlan.basic();
}
else {
  plan = customer.getPlan();
}
```

**After**
```unknown
class NullCustomer extends Customer {
  isNull(): boolean {
    return true;
  }
  getPlan(): Plan {
    return new NullPlan();
  }
  // Some other NULL functionality.
}

// Replace null values with Null-object.
let customer = (order.customer != null) ?
  order.customer : new NullCustomer();

// Use Null-object as if it's normal subclass.
plan = customer.getPlan();
```
