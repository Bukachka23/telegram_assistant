# Replace Exception with Test

**URL:** https://refactoring.guru/replace-exception-with-test
**Type:** technique  |  **Category:** Simplifying Method Calls


## Replace Exception with Test

Problem You throw an exception in a place where a simple test would do the job? Solution Replace the exception with a condition test. Before double getValueForPeriod(int periodNumber) {
  try {
    return values[periodNumber];
  } catch (ArrayIndexOutOfBoundsException e) {
    return 0;
  }
} After double getValueForPeriod(int periodNumber) {
  if (periodNumber >= values.length) {
    return 0;
  }
  return values[periodNumber];
} Before double GetValueForPeriod(int periodNumber) 
{
  try 
  {
    return values[periodNumber];
  } 
  catch (IndexOutOfRangeException e) 
  {
    return 0;
  }
} After double GetValueForPeriod(int periodNumber) 
{
  if (periodNumber >= values.Length) 
  {
    return 0;
  }
  return values[periodNumber];
} Before function getValueForPeriod($periodNumber) {
  try {
    return $this->values[$periodNumber];
  } catch (ArrayIndexOutOfBoundsException $e) {
    return 0;
  }
} After function getValueForPeriod($periodNumber) {
  if ($periodNumber >= count($this->values)) {
    return 0;
  }
  return $this->values[$periodNumber];
} Before def getValueForPeriod(periodNumber):
    try:
        return values[periodNumber]
    except IndexError:
        return 0 After def getValueForPeriod(self, periodNumber):
    if periodNumber >= len(self.values):
        return 0
    return self.values[periodNumber] Before getValueForPeriod(periodNumber: number): number {
  try {
    return values[periodNumber];
  } catch (ArrayIndexOutOfBoundsException e) {
    return 0;
  }
} After getValueForPeriod(periodNumber: number): number {
  if (periodNumber >= values.length) {
    return 0;
  }
  return values[periodNumber];
}


## Why Refactor

Exceptions should be used to handle irregular behavior related to an unexpected error. They shouldn’t serve as a replacement for testing. If an exception can be avoided by simply verifying a condition before running, then do so. Exceptions should be reserved for real errors. For instance, you entered a minefield and triggered a mine there, resulting in an exception; the exception was successfully handled and you were lifted through the air to safety beyond the mine field. But you could have avoided this all by simply reading the warning sign in front of the minefield to begin with.


## Benefits

A simple conditional can sometimes be more obvious than exception handling code.


## How to Refactor

Create a conditional for an edge case and move it before the try/catch block. Move code from the catch section inside this conditional. In the catch section, place the code for throwing a usual unnamed exception and run all the tests. If no exceptions were thrown during the tests, get rid of the try / catch operator.


## Code Examples

### unknown

**Before**
```unknown
double getValueForPeriod(int periodNumber) {
  try {
    return values[periodNumber];
  } catch (ArrayIndexOutOfBoundsException e) {
    return 0;
  }
}
```

**After**
```unknown
double getValueForPeriod(int periodNumber) {
  if (periodNumber >= values.length) {
    return 0;
  }
  return values[periodNumber];
}
```

### unknown

**Before**
```unknown
double GetValueForPeriod(int periodNumber) 
{
  try 
  {
    return values[periodNumber];
  } 
  catch (IndexOutOfRangeException e) 
  {
    return 0;
  }
}
```

**After**
```unknown
double GetValueForPeriod(int periodNumber) 
{
  if (periodNumber >= values.Length) 
  {
    return 0;
  }
  return values[periodNumber];
}
```

### unknown

**Before**
```unknown
function getValueForPeriod($periodNumber) {
  try {
    return $this->values[$periodNumber];
  } catch (ArrayIndexOutOfBoundsException $e) {
    return 0;
  }
}
```

**After**
```unknown
function getValueForPeriod($periodNumber) {
  if ($periodNumber >= count($this->values)) {
    return 0;
  }
  return $this->values[$periodNumber];
}
```

### unknown

**Before**
```unknown
def getValueForPeriod(periodNumber):
    try:
        return values[periodNumber]
    except IndexError:
        return 0
```

**After**
```unknown
def getValueForPeriod(self, periodNumber):
    if periodNumber >= len(self.values):
        return 0
    return self.values[periodNumber]
```

### unknown

**Before**
```unknown
getValueForPeriod(periodNumber: number): number {
  try {
    return values[periodNumber];
  } catch (ArrayIndexOutOfBoundsException e) {
    return 0;
  }
}
```

**After**
```unknown
getValueForPeriod(periodNumber: number): number {
  if (periodNumber >= values.length) {
    return 0;
  }
  return values[periodNumber];
}
```
