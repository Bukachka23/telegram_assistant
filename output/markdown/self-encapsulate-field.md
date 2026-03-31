# Self Encapsulate Field

**URL:** https://refactoring.guru/self-encapsulate-field
**Type:** technique  |  **Category:** Organizing Data


## Self Encapsulate Field

Self-encapsulation is distinct from ordinary Encapsulate Field : the refactoring technique given here is performed on a private field. Problem You use direct access to private fields inside a class. Solution Create a getter and setter for the field, and use only them for accessing the field. Before class Range {
  private int low, high;
  boolean includes(int arg) {
    return arg >= low && arg <= high;
  }
} After class Range {
  private int low, high;
  boolean includes(int arg) {
    return arg >= getLow() && arg <= getHigh();
  }
  int getLow() {
    return low;
  }
  int getHigh() {
    return high;
  }
} Before class Range 
{
  private int low, high;
  
  bool Includes(int arg) 
  {
    return arg >= low && arg <= high;
  }
} After class Range 
{
  private int low, high;
  
  int Low {
    get { return low; }
  }
  int High {
    get { return high; }
  }
  
  bool Includes(int arg) 
  {
    return arg >= Low && arg <= High;
  }
} Before private $low;
private $high;

function includes($arg) {
  return $arg >= $this->low && $arg <= $this->high;
} After private $low;
private $high;

function includes($arg) {
  return $arg >= $this->getLow() && $arg <= $this->getHigh();
}
function getLow() {
  return $this->low;
}
function getHigh() {
  return $this->high;
} Before class Range {
  private low: number
  private high: number;
  includes(arg: number): boolean {
    return arg >= low && arg <= high;
  }
} After class Range {
  private low: number
  private high: number;
  includes(arg: number): boolean {
    return arg >= getLow() && arg <= getHigh();
  }
  getLow(): number {
    return low;
  }
  getHigh(): number {
    return high;
  }
}


## Why Refactor

Sometimes directly accessing a private field inside a class just isn’t flexible enough. You want to be able to initiate a field value when the first query is made or perform certain operations on new values of the field when they’re assigned, or maybe do all this in various ways in subclasses.


## Benefits

Indirect access to fields is when a field is acted on via access methods (getters and setters). This approach is much more flexible than direct access to fields . First, you can perform complex operations when data in the field is set or received. Lazy initialization and validation of field values are easily implemented inside field getters and setters. Second and more crucially, you can redefine getters and setters in subclasses. You have the option of not implementing a setter for a field at all. The field value will be specified only in the constructor, thus making the field unchangeable throughout the entire object lifespan.


## Drawbacks

When direct access to fields is used, code looks simpler and more presentable, although flexibility is diminished.


## How to Refactor

Create a getter (and optional setter) for the field. They should be either protected or public . Find all direct invocations of the field and replace them with getter and setter calls.


## Code Examples

### unknown

**Before**
```unknown
class Range {
  private int low, high;
  boolean includes(int arg) {
    return arg >= low && arg <= high;
  }
}
```

**After**
```unknown
class Range {
  private int low, high;
  boolean includes(int arg) {
    return arg >= getLow() && arg <= getHigh();
  }
  int getLow() {
    return low;
  }
  int getHigh() {
    return high;
  }
}
```

### unknown

**Before**
```unknown
class Range 
{
  private int low, high;
  
  bool Includes(int arg) 
  {
    return arg >= low && arg <= high;
  }
}
```

**After**
```unknown
class Range 
{
  private int low, high;
  
  int Low {
    get { return low; }
  }
  int High {
    get { return high; }
  }
  
  bool Includes(int arg) 
  {
    return arg >= Low && arg <= High;
  }
}
```

### unknown

**Before**
```unknown
private $low;
private $high;

function includes($arg) {
  return $arg >= $this->low && $arg <= $this->high;
}
```

**After**
```unknown
private $low;
private $high;

function includes($arg) {
  return $arg >= $this->getLow() && $arg <= $this->getHigh();
}
function getLow() {
  return $this->low;
}
function getHigh() {
  return $this->high;
}
```

### unknown

**Before**
```unknown
class Range {
  private low: number
  private high: number;
  includes(arg: number): boolean {
    return arg >= low && arg <= high;
  }
}
```

**After**
```unknown
class Range {
  private low: number
  private high: number;
  includes(arg: number): boolean {
    return arg >= getLow() && arg <= getHigh();
  }
  getLow(): number {
    return low;
  }
  getHigh(): number {
    return high;
  }
}
```
