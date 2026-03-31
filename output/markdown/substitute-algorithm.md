# Substitute Algorithm

**URL:** https://refactoring.guru/substitute-algorithm
**Type:** technique  |  **Category:** Composing Methods


## Substitute Algorithm

Problem So you want to replace an existing algorithm with a new one? Solution Replace the body of the method that implements the algorithm with a new algorithm. Before String foundPerson(String[] people){
  for (int i = 0; i < people.length; i++) {
    if (people[i].equals("Don")){
      return "Don";
    }
    if (people[i].equals("John")){
      return "John";
    }
    if (people[i].equals("Kent")){
      return "Kent";
    }
  }
  return "";
} After String foundPerson(String[] people){
  List candidates =
    Arrays.asList(new String[] {"Don", "John", "Kent"});
  for (int i=0; i < people.length; i++) {
    if (candidates.contains(people[i])) {
      return people[i];
    }
  }
  return "";
} Before string FoundPerson(string[] people)
{
  for (int i = 0; i < people.Length; i++) 
  {
    if (people[i].Equals("Don"))
    {
      return "Don";
    }
    if (people[i].Equals("John"))
    {
      return "John";
    }
    if (people[i].Equals("Kent"))
    {
      return "Kent";
    }
  }
  return String.Empty;
} After string FoundPerson(string[] people)
{
  List<string> candidates = new List<string>() {"Don", "John", "Kent"};
  
  for (int i = 0; i < people.Length; i++) 
  {
    if (candidates.Contains(people[i])) 
    {
      return people[i];
    }
  }
  
  return String.Empty;
} Before function foundPerson(array $people){
  for ($i = 0; $i < count($people); $i++) {
    if ($people[$i] === "Don") {
      return "Don";
    }
    if ($people[$i] === "John") {
      return "John";
    }
    if ($people[$i] === "Kent") {
      return "Kent";
    }
  }
  return "";
} After function foundPerson(array $people){
  foreach (["Don", "John", "Kent"] as $needle) {
    $id = array_search($needle, $people, true);
    if ($id !== false) {
      return $people[$id];
    }
  }
  return "";
} Before def foundPerson(people):
    for i in range(len(people)):
        if people[i] == "Don":
            return "Don"
        if people[i] == "John":
            return "John"
        if people[i] == "Kent":
            return "Kent"
    return "" After def foundPerson(people):
    candidates = ["Don", "John", "Kent"]
    return people if people in candidates else "" Before foundPerson(people: string[]): string{
  for (let person of people) {
    if (person.equals("Don")){
      return "Don";
    }
    if (person.equals("John")){
      return "John";
    }
    if (person.equals("Kent")){
      return "Kent";
    }
  }
  return "";
} After foundPerson(people: string[]): string{
  let candidates = ["Don", "John", "Kent"];
  for (let person of people) {
    if (candidates.includes(person)) {
      return person;
    }
  }
  return "";
}


## Why Refactor

Gradual refactoring isn’t the only method for improving a program. Sometimes a method is so cluttered with issues that it’s easier to tear down the method and start fresh. And perhaps you have found an algorithm that’s much simpler and more efficient. If this is the case, you should simply replace the old algorithm with the new one. As time goes on, your algorithm may be incorporated into a well-known library or framework and you want to get rid of your independent implementation, in order to simplify maintenance. The requirements for your program may change so heavily that your existing algorithm can’t be salvaged for the task.


## How to Refactor

Make sure that you have simplified the existing algorithm as much as possible. Move unimportant code to other methods using Extract Method . The fewer moving parts in your algorithm, the easier it’s to replace. Create your new algorithm in a new method. Replace the old algorithm with the new one and start testing the program. If the results don’t match, return to the old implementation and compare the results. Identify the causes of the discrepancy. While the cause is often an error in the old algorithm, it’s more likely due to something not working in the new one. When all tests are successfully completed, delete the old algorithm for good!


## Code Examples

### unknown

**Before**
```unknown
String foundPerson(String[] people){
  for (int i = 0; i < people.length; i++) {
    if (people[i].equals("Don")){
      return "Don";
    }
    if (people[i].equals("John")){
      return "John";
    }
    if (people[i].equals("Kent")){
      return "Kent";
    }
  }
  return "";
}
```

**After**
```unknown
String foundPerson(String[] people){
  List candidates =
    Arrays.asList(new String[] {"Don", "John", "Kent"});
  for (int i=0; i < people.length; i++) {
    if (candidates.contains(people[i])) {
      return people[i];
    }
  }
  return "";
}
```

### unknown

**Before**
```unknown
string FoundPerson(string[] people)
{
  for (int i = 0; i < people.Length; i++) 
  {
    if (people[i].Equals("Don"))
    {
      return "Don";
    }
    if (people[i].Equals("John"))
    {
      return "John";
    }
    if (people[i].Equals("Kent"))
    {
      return "Kent";
    }
  }
  return String.Empty;
}
```

**After**
```unknown
string FoundPerson(string[] people)
{
  List<string> candidates = new List<string>() {"Don", "John", "Kent"};
  
  for (int i = 0; i < people.Length; i++) 
  {
    if (candidates.Contains(people[i])) 
    {
      return people[i];
    }
  }
  
  return String.Empty;
}
```

### unknown

**Before**
```unknown
function foundPerson(array $people){
  for ($i = 0; $i < count($people); $i++) {
    if ($people[$i] === "Don") {
      return "Don";
    }
    if ($people[$i] === "John") {
      return "John";
    }
    if ($people[$i] === "Kent") {
      return "Kent";
    }
  }
  return "";
}
```

**After**
```unknown
function foundPerson(array $people){
  foreach (["Don", "John", "Kent"] as $needle) {
    $id = array_search($needle, $people, true);
    if ($id !== false) {
      return $people[$id];
    }
  }
  return "";
}
```

### unknown

**Before**
```unknown
def foundPerson(people):
    for i in range(len(people)):
        if people[i] == "Don":
            return "Don"
        if people[i] == "John":
            return "John"
        if people[i] == "Kent":
            return "Kent"
    return ""
```

**After**
```unknown
def foundPerson(people):
    candidates = ["Don", "John", "Kent"]
    return people if people in candidates else ""
```

### unknown

**Before**
```unknown
foundPerson(people: string[]): string{
  for (let person of people) {
    if (person.equals("Don")){
      return "Don";
    }
    if (person.equals("John")){
      return "John";
    }
    if (person.equals("Kent")){
      return "Kent";
    }
  }
  return "";
}
```

**After**
```unknown
foundPerson(people: string[]): string{
  let candidates = ["Don", "John", "Kent"];
  for (let person of people) {
    if (candidates.includes(person)) {
      return person;
    }
  }
  return "";
}
```
