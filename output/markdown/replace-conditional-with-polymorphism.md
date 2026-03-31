# Replace Conditional with Polymorphism

**URL:** https://refactoring.guru/replace-conditional-with-polymorphism
**Type:** technique  |  **Category:** Simplifying Conditional Expressions


## Replace Conditional with Polymorphism

Problem You have a conditional that performs various actions depending on object type or properties. Solution Create subclasses matching the branches of the conditional. In them, create a shared method and move code from the corresponding branch of the conditional to it. Then replace the conditional with the relevant method call. The result is that the proper implementation will be attained via polymorphism depending on the object class. Before class Bird {
  // ...
  double getSpeed() {
    switch (type) {
      case EUROPEAN:
        return getBaseSpeed();
      case AFRICAN:
        return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return (isNailed) ? 0 : getBaseSpeed(voltage);
    }
    throw new RuntimeException("Should be unreachable");
  }
} After abstract class Bird {
  // ...
  abstract double getSpeed();
}

class European extends Bird {
  double getSpeed() {
    return getBaseSpeed();
  }
}
class African extends Bird {
  double getSpeed() {
    return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
  }
}
class NorwegianBlue extends Bird {
  double getSpeed() {
    return (isNailed) ? 0 : getBaseSpeed(voltage);
  }
}

// Somewhere in client code
speed = bird.getSpeed(); Before public class Bird 
{
  // ...
  public double GetSpeed() 
  {
    switch (type) 
    {
      case EUROPEAN:
        return GetBaseSpeed();
      case AFRICAN:
        return GetBaseSpeed() - GetLoadFactor() * numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return isNailed ? 0 : GetBaseSpeed(voltage);
      default:
        throw new Exception("Should be unreachable");
    }
  }
} After public abstract class Bird 
{
  // ...
  public abstract double GetSpeed();
}

class European: Bird 
{
  public override double GetSpeed() 
  {
    return GetBaseSpeed();
  }
}
class African: Bird 
{
  public override double GetSpeed() 
  {
    return GetBaseSpeed() - GetLoadFactor() * numberOfCoconuts;
  }
}
class NorwegianBlue: Bird
{
  public override double GetSpeed() 
  {
    return isNailed ? 0 : GetBaseSpeed(voltage);
  }
}

// Somewhere in client code
speed = bird.GetSpeed(); Before class Bird {
  // ...
  public function getSpeed() {
    switch ($this->type) {
      case EUROPEAN:
        return $this->getBaseSpeed();
      case AFRICAN:
        return $this->getBaseSpeed() - $this->getLoadFactor() * $this->numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return ($this->isNailed) ? 0 : $this->getBaseSpeed($this->voltage);
    }
    throw new Exception("Should be unreachable");
  }
  // ...
} After abstract class Bird {
  // ...
  abstract function getSpeed();
  // ...
}

class European extends Bird {
  public function getSpeed() {
    return $this->getBaseSpeed();
  }
}
class African extends Bird {
  public function getSpeed() {
    return $this->getBaseSpeed() - $this->getLoadFactor() * $this->numberOfCoconuts;
  }
}
class NorwegianBlue extends Bird {
  public function getSpeed() {
    return ($this->isNailed) ? 0 : $this->getBaseSpeed($this->voltage);
  }
}

// Somewhere in Client code.
$speed = $bird->getSpeed(); Before class Bird:
    # ...
    def getSpeed(self):
        if self.type == EUROPEAN:
            return self.getBaseSpeed()
        elif self.type == AFRICAN:
            return self.getBaseSpeed() - self.getLoadFactor() * self.numberOfCoconuts
        elif self.type == NORWEGIAN_BLUE:
            return 0 if self.isNailed else self.getBaseSpeed(self.voltage)
        else:
            raise Exception("Should be unreachable") After class Bird:
    # ...
    def getSpeed(self):
        pass

class European(Bird):
    def getSpeed(self):
        return self.getBaseSpeed()
    
    
class African(Bird):
    def getSpeed(self):
        return self.getBaseSpeed() - self.getLoadFactor() * self.numberOfCoconuts


class NorwegianBlue(Bird):
    def getSpeed(self):
        return 0 if self.isNailed else self.getBaseSpeed(self.voltage)

# Somewhere in client code
speed = bird.getSpeed() Before class Bird {
  // ...
  getSpeed(): number {
    switch (type) {
      case EUROPEAN:
        return getBaseSpeed();
      case AFRICAN:
        return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return (isNailed) ? 0 : getBaseSpeed(voltage);
    }
    throw new Error("Should be unreachable");
  }
} After abstract class Bird {
  // ...
  abstract getSpeed(): number;
}

class European extends Bird {
  getSpeed(): number {
    return getBaseSpeed();
  }
}
class African extends Bird {
  getSpeed(): number {
    return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
  }
}
class NorwegianBlue extends Bird {
  getSpeed(): number {
    return (isNailed) ? 0 : getBaseSpeed(voltage);
  }
}

// Somewhere in client code
let speed = bird.getSpeed();


## Why Refactor

This refactoring technique can help if your code contains operators performing various tasks that vary based on: Class of the object or interface that it implements Value of an object’s field Result of calling one of an object’s methods If a new object property or type appears, you will need to search for and add code in all similar conditionals. Thus the benefit of this technique is multiplied if there are multiple conditionals scattered throughout all of an object’s methods.


## Benefits

This technique adheres to the Tell-Don’t-Ask principle: instead of asking an object about its state and then performing actions based on this, it’s much easier to simply tell the object what it needs to do and let it decide for itself how to do that. Removes duplicate code. You get rid of many almost identical conditionals. If you need to add a new execution variant, all you need to do is add a new subclass without touching the existing code ( Open/Closed Principle ).


## Preparing to Refactor

For this refactoring technique, you should have a ready hierarchy of classes that will contain alternative behaviors. If you don’t have a hierarchy like this, create one. Other techniques will help to make this happen: Replace Type Code with Subclasses . Subclasses will be created for all values of a particular object property. This approach is simple but less flexible since you can’t create subclasses for the other properties of the object. Replace Type Code with State/Strategy . A class will be dedicated for a particular object property and subclasses will be created from it for each value of the property. The current class will contain references to the objects of this type and delegate execution to them. The following steps assume that you have already created the hierarchy.


## Refactoring Steps

If the conditional is in a method that performs other actions as well, perform Extract Method . For each hierarchy subclass, redefine the method that contains the conditional and copy the code of the corresponding conditional branch to that location. Delete this branch from the conditional. Repeat replacement until the conditional is empty. Then delete the conditional and declare the method abstract.


## Code Examples

### unknown

**Before**
```unknown
class Bird {
  // ...
  double getSpeed() {
    switch (type) {
      case EUROPEAN:
        return getBaseSpeed();
      case AFRICAN:
        return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return (isNailed) ? 0 : getBaseSpeed(voltage);
    }
    throw new RuntimeException("Should be unreachable");
  }
}
```

**After**
```unknown
abstract class Bird {
  // ...
  abstract double getSpeed();
}

class European extends Bird {
  double getSpeed() {
    return getBaseSpeed();
  }
}
class African extends Bird {
  double getSpeed() {
    return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
  }
}
class NorwegianBlue extends Bird {
  double getSpeed() {
    return (isNailed) ? 0 : getBaseSpeed(voltage);
  }
}

// Somewhere in client code
speed = bird.getSpeed();
```

### unknown

**Before**
```unknown
public class Bird 
{
  // ...
  public double GetSpeed() 
  {
    switch (type) 
    {
      case EUROPEAN:
        return GetBaseSpeed();
      case AFRICAN:
        return GetBaseSpeed() - GetLoadFactor() * numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return isNailed ? 0 : GetBaseSpeed(voltage);
      default:
        throw new Exception("Should be unreachable");
    }
  }
}
```

**After**
```unknown
public abstract class Bird 
{
  // ...
  public abstract double GetSpeed();
}

class European: Bird 
{
  public override double GetSpeed() 
  {
    return GetBaseSpeed();
  }
}
class African: Bird 
{
  public override double GetSpeed() 
  {
    return GetBaseSpeed() - GetLoadFactor() * numberOfCoconuts;
  }
}
class NorwegianBlue: Bird
{
  public override double GetSpeed() 
  {
    return isNailed ? 0 : GetBaseSpeed(voltage);
  }
}

// Somewhere in client code
speed = bird.GetSpeed();
```

### unknown

**Before**
```unknown
class Bird {
  // ...
  public function getSpeed() {
    switch ($this->type) {
      case EUROPEAN:
        return $this->getBaseSpeed();
      case AFRICAN:
        return $this->getBaseSpeed() - $this->getLoadFactor() * $this->numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return ($this->isNailed) ? 0 : $this->getBaseSpeed($this->voltage);
    }
    throw new Exception("Should be unreachable");
  }
  // ...
}
```

**After**
```unknown
abstract class Bird {
  // ...
  abstract function getSpeed();
  // ...
}

class European extends Bird {
  public function getSpeed() {
    return $this->getBaseSpeed();
  }
}
class African extends Bird {
  public function getSpeed() {
    return $this->getBaseSpeed() - $this->getLoadFactor() * $this->numberOfCoconuts;
  }
}
class NorwegianBlue extends Bird {
  public function getSpeed() {
    return ($this->isNailed) ? 0 : $this->getBaseSpeed($this->voltage);
  }
}

// Somewhere in Client code.
$speed = $bird->getSpeed();
```

### unknown

**Before**
```unknown
class Bird:
    # ...
    def getSpeed(self):
        if self.type == EUROPEAN:
            return self.getBaseSpeed()
        elif self.type == AFRICAN:
            return self.getBaseSpeed() - self.getLoadFactor() * self.numberOfCoconuts
        elif self.type == NORWEGIAN_BLUE:
            return 0 if self.isNailed else self.getBaseSpeed(self.voltage)
        else:
            raise Exception("Should be unreachable")
```

**After**
```unknown
class Bird:
    # ...
    def getSpeed(self):
        pass

class European(Bird):
    def getSpeed(self):
        return self.getBaseSpeed()
    
    
class African(Bird):
    def getSpeed(self):
        return self.getBaseSpeed() - self.getLoadFactor() * self.numberOfCoconuts


class NorwegianBlue(Bird):
    def getSpeed(self):
        return 0 if self.isNailed else self.getBaseSpeed(self.voltage)

# Somewhere in client code
speed = bird.getSpeed()
```

### unknown

**Before**
```unknown
class Bird {
  // ...
  getSpeed(): number {
    switch (type) {
      case EUROPEAN:
        return getBaseSpeed();
      case AFRICAN:
        return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
      case NORWEGIAN_BLUE:
        return (isNailed) ? 0 : getBaseSpeed(voltage);
    }
    throw new Error("Should be unreachable");
  }
}
```

**After**
```unknown
abstract class Bird {
  // ...
  abstract getSpeed(): number;
}

class European extends Bird {
  getSpeed(): number {
    return getBaseSpeed();
  }
}
class African extends Bird {
  getSpeed(): number {
    return getBaseSpeed() - getLoadFactor() * numberOfCoconuts;
  }
}
class NorwegianBlue extends Bird {
  getSpeed(): number {
    return (isNailed) ? 0 : getBaseSpeed(voltage);
  }
}

// Somewhere in client code
let speed = bird.getSpeed();
```
