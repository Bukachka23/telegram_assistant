# Encapsulate Field

**URL:** https://refactoring.guru/encapsulate-field
**Type:** technique  |  **Category:** Organizing Data


## Encapsulate Field

Problem You have a public field. Solution Make the field private and create access methods for it. Before class Person {
  public String name;
} After class Person {
  private String name;

  public String getName() {
    return name;
  }
  public void setName(String arg) {
    name = arg;
  }
} Before class Person 
{
  public string name;
} After class Person 
{
  private string name;

  public string Name
  {
    get { return name; }
    set { name = value; }
  }
} Before public $name; After private $name;

public getName() {
  return $this->name;
}

public setName($arg) {
  $this->name = $arg;
} Before class Person {
  name: string;
} After class Person {
  private _name: string;

  get name() {
    return this._name;
  }
  setName(arg: string): void {
    this._name = arg;
  }
}


## Why Refactor

One of the pillars of object-oriented programming is Encapsulation , the ability to conceal object data. Otherwise, all objects would be public and other objects could get and modify the data of your object without any checks and balances! Data is separated from the behaviors associated with this data, modularity of program sections is compromised, and maintenance becomes complicated.


## Benefits

If the data and behavior of a component are closely interrelated and are in the same place in the code, it’s much easier for you to maintain and develop this component. You can also perform complicated operations related to access to object fields.


## When Not to Use

In some cases, encapsulation is ill-advised due to performance considerations. These cases are rare but when they happen, this circumstance is very important. Say that you have a graphical editor that contains objects possessing x- and y-coordinates. These fields are unlikely to change in the future. What’s more, the program involves a great many different objects in which these fields are present. So accessing the coordinate fields directly saves significant CPU cycles that would otherwise be taken up by calling access methods. As an example of this unusual case, there’s the Point class in Java. All fields of this class are public.


## How to Refactor

Create a getter and setter for the field. Find all invocations of the field. Replace receipt of the field value with the getter, and replace setting of new field values with the setter. After all field invocations have been replaced, make the field private.


## Next Steps

Encapsulate Field is only the first step in bringing data and the behaviors involving this data closer together. After you create simple methods for access fields, you should recheck the places where these methods are called. It’s quite possible that the code in these areas would look more appropriate in the access methods.


## Code Examples

### unknown

**Before**
```unknown
class Person {
  public String name;
}
```

**After**
```unknown
class Person {
  private String name;

  public String getName() {
    return name;
  }
  public void setName(String arg) {
    name = arg;
  }
}
```

### unknown

**Before**
```unknown
class Person 
{
  public string name;
}
```

**After**
```unknown
class Person 
{
  private string name;

  public string Name
  {
    get { return name; }
    set { name = value; }
  }
}
```

### unknown

**Before**
```unknown
public $name;
```

**After**
```unknown
private $name;

public getName() {
  return $this->name;
}

public setName($arg) {
  $this->name = $arg;
}
```

### unknown

**Before**
```unknown
class Person {
  name: string;
}
```

**After**
```unknown
class Person {
  private _name: string;

  get name() {
    return this._name;
  }
  setName(arg: string): void {
    this._name = arg;
  }
}
```
