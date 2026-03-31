# Split Temporary Variable

**URL:** https://refactoring.guru/split-temporary-variable
**Type:** technique  |  **Category:** Composing Methods


## Split Temporary Variable

Problem You have a local variable that’s used to store various intermediate values inside a method (except for cycle variables). Solution Use different variables for different values. Each variable should be responsible for only one particular thing. Before double temp = 2 * (height + width);
System.out.println(temp);
temp = height * width;
System.out.println(temp); After final double perimeter = 2 * (height + width);
System.out.println(perimeter);
final double area = height * width;
System.out.println(area); Before double temp = 2 * (height + width);
Console.WriteLine(temp);
temp = height * width;
Console.WriteLine(temp); After readonly double perimeter = 2 * (height + width);
Console.WriteLine(perimeter);
readonly double area = height * width;
Console.WriteLine(area); Before $temp = 2 * ($this->height + $this->width);
echo $temp;
$temp = $this->height * $this->width;
echo $temp; After $perimeter = 2 * ($this->height + $this->width);
echo $perimeter;
$area = $this->height * $this->width;
echo $area; Before temp = 2 * (height + width)
print(temp)
temp = height * width
print(temp) After perimeter = 2 * (height + width)
print(perimeter)
area = height * width
print(area) Before let temp = 2 * (height + width);
console.log(temp);
temp = height * width;
console.log(temp); After const perimeter = 2 * (height + width);
console.log(perimeter);
const area = height * width;
console.log(area);


## Why Refactor

If you’re skimping on the number of variables inside a function and reusing them for various unrelated purposes, you’re sure to encounter problems as soon as you need to make changes to the code containing the variables. You will have to recheck each case of variable use to make sure that the correct values are used.


## Benefits

Each component of the program code should be responsible for one and one thing only. This makes it much easier to maintain the code, since you can easily replace any particular thing without fear of unintended effects. Code becomes more readable. If a variable was created long ago in a rush, it probably has a name that doesn’t explain anything: k , a2 , value , etc. But you can fix this situation by naming the new variables in an understandable, self-explanatory way. Such names might resemble customerTaxValue , cityUnemploymentRate , clientSalutationString and the like. This refactoring technique is useful if you anticipate using Extract Method later.


## How to Refactor

Find the first place in the code where the variable is given a value. Here you should rename the variable with a name that corresponds to the value being assigned. Use the new name instead of the old one in places where this value of the variable is used. Repeat as needed for places where the variable is assigned a different value.


## Code Examples

### unknown

**Before**
```unknown
double temp = 2 * (height + width);
System.out.println(temp);
temp = height * width;
System.out.println(temp);
```

**After**
```unknown
final double perimeter = 2 * (height + width);
System.out.println(perimeter);
final double area = height * width;
System.out.println(area);
```

### unknown

**Before**
```unknown
double temp = 2 * (height + width);
Console.WriteLine(temp);
temp = height * width;
Console.WriteLine(temp);
```

**After**
```unknown
readonly double perimeter = 2 * (height + width);
Console.WriteLine(perimeter);
readonly double area = height * width;
Console.WriteLine(area);
```

### unknown

**Before**
```unknown
$temp = 2 * ($this->height + $this->width);
echo $temp;
$temp = $this->height * $this->width;
echo $temp;
```

**After**
```unknown
$perimeter = 2 * ($this->height + $this->width);
echo $perimeter;
$area = $this->height * $this->width;
echo $area;
```

### unknown

**Before**
```unknown
temp = 2 * (height + width)
print(temp)
temp = height * width
print(temp)
```

**After**
```unknown
perimeter = 2 * (height + width)
print(perimeter)
area = height * width
print(area)
```

### unknown

**Before**
```unknown
let temp = 2 * (height + width);
console.log(temp);
temp = height * width;
console.log(temp);
```

**After**
```unknown
const perimeter = 2 * (height + width);
console.log(perimeter);
const area = height * width;
console.log(area);
```
