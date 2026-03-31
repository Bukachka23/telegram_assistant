# Replace Magic Number with Symbolic Constant

**URL:** https://refactoring.guru/replace-magic-number-with-symbolic-constant
**Type:** technique  |  **Category:** Organizing Data


## Replace Magic Number with Symbolic Constant

Problem Your code uses a number that has a certain meaning to it. Solution Replace this number with a constant that has a human-readable name explaining the meaning of the number. Before double potentialEnergy(double mass, double height) {
  return mass * height * 9.81;
} After static final double GRAVITATIONAL_CONSTANT = 9.81;

double potentialEnergy(double mass, double height) {
  return mass * height * GRAVITATIONAL_CONSTANT;
} Before double PotentialEnergy(double mass, double height) 
{
  return mass * height * 9.81;
} After const double GRAVITATIONAL_CONSTANT = 9.81;

double PotentialEnergy(double mass, double height) 
{
  return mass * height * GRAVITATIONAL_CONSTANT;
} Before function potentialEnergy($mass, $height) {
  return $mass * $height * 9.81;
} After define("GRAVITATIONAL_CONSTANT", 9.81);

function potentialEnergy($mass, $height) {
  return $mass * $height * GRAVITATIONAL_CONSTANT;
} Before def potentialEnergy(mass, height):
    return mass * height * 9.81 After GRAVITATIONAL_CONSTANT = 9.81

def potentialEnergy(mass, height):
    return mass * height * GRAVITATIONAL_CONSTANT Before potentialEnergy(mass: number, height: number): number {
  return mass * height * 9.81;
} After static const GRAVITATIONAL_CONSTANT = 9.81;

potentialEnergy(mass: number, height: number): number {
  return mass * height * GRAVITATIONAL_CONSTANT;
}


## Why Refactor

A magic number is a numeric value that’s encountered in the source but has no obvious meaning. This “anti-pattern” makes it harder to understand the program and refactor the code. Yet more difficulties arise when you need to change this magic number. Find and replace won’t work for this: the same number may be used for different purposes in different places, meaning that you will have to verify every line of code that uses this number.


## Benefits

The symbolic constant can serve as live documentation of the meaning of its value. It’s much easier to change the value of a constant than to search for this number throughout the entire codebase, without the risk of accidentally changing the same number used elsewhere for a different purpose. Reduce duplicate use of a number or string in the code. This is especially important when the value is complicated and long (such as 3.14159 or 0xCAFEBABE ).


## Not all numbers are magical.

If the purpose of a number is obvious, there’s no need to replace it. A classic example is: for (i = 0; i < сount; i++) { ... }


## Alternatives

Sometimes a magic number can be replaced with method calls. For example, if you have a magic number that signifies the number of elements in a collection, you don’t need to use it for checking the last element of the collection. Instead, use the standard method for getting the collection length. Magic numbers are sometimes used as type code. Say that you have two types of users and you use a number field in a class to specify which is which: administrators are 1 and ordinary users are 2 . In this case, you should use one of the refactoring methods to avoid type code: Replace Type Code with Class Replace Type Code with Subclasses Replace Type Code with State/Strategy


## How to Refactor

Declare a constant and assign the value of the magic number to it. Find all mentions of the magic number. For each of the numbers that you find, double-check that the magic number in this particular case corresponds to the purpose of the constant. If yes, replace the number with your constant. This is an important step, since the same number can mean absolutely different things (and replaced with different constants, as the case may be).


## Code Examples

### unknown

**Before**
```unknown
double potentialEnergy(double mass, double height) {
  return mass * height * 9.81;
}
```

**After**
```unknown
static final double GRAVITATIONAL_CONSTANT = 9.81;

double potentialEnergy(double mass, double height) {
  return mass * height * GRAVITATIONAL_CONSTANT;
}
```

### unknown

**Before**
```unknown
double PotentialEnergy(double mass, double height) 
{
  return mass * height * 9.81;
}
```

**After**
```unknown
const double GRAVITATIONAL_CONSTANT = 9.81;

double PotentialEnergy(double mass, double height) 
{
  return mass * height * GRAVITATIONAL_CONSTANT;
}
```

### unknown

**Before**
```unknown
function potentialEnergy($mass, $height) {
  return $mass * $height * 9.81;
}
```

**After**
```unknown
define("GRAVITATIONAL_CONSTANT", 9.81);

function potentialEnergy($mass, $height) {
  return $mass * $height * GRAVITATIONAL_CONSTANT;
}
```

### unknown

**Before**
```unknown
def potentialEnergy(mass, height):
    return mass * height * 9.81
```

**After**
```unknown
GRAVITATIONAL_CONSTANT = 9.81

def potentialEnergy(mass, height):
    return mass * height * GRAVITATIONAL_CONSTANT
```

### unknown

**Before**
```unknown
potentialEnergy(mass: number, height: number): number {
  return mass * height * 9.81;
}
```

**After**
```unknown
static const GRAVITATIONAL_CONSTANT = 9.81;

potentialEnergy(mass: number, height: number): number {
  return mass * height * GRAVITATIONAL_CONSTANT;
}
```
