# Replace Parameter with Method Call

**URL:** https://refactoring.guru/replace-parameter-with-method-call
**Type:** technique  |  **Category:** Simplifying Method Calls


## Replace Parameter with Method Call

Problem Calling a query method and passing its results as the parameters of another method, while that method could call the query directly. Solution Instead of passing the value through a parameter, try placing a query call inside the method body. Before int basePrice = quantity * itemPrice;
double seasonDiscount = this.getSeasonalDiscount();
double fees = this.getFees();
double finalPrice = discountedPrice(basePrice, seasonDiscount, fees); After int basePrice = quantity * itemPrice;
double finalPrice = discountedPrice(basePrice); Before int basePrice = quantity * itemPrice;
double seasonDiscount = this.GetSeasonalDiscount();
double fees = this.GetFees();
double finalPrice = DiscountedPrice(basePrice, seasonDiscount, fees); After int basePrice = quantity * itemPrice;
double finalPrice = DiscountedPrice(basePrice); Before $basePrice = $this->quantity * $this->itemPrice;
$seasonDiscount = $this->getSeasonalDiscount();
$fees = $this->getFees();
$finalPrice = $this->discountedPrice($basePrice, $seasonDiscount, $fees); After $basePrice = $this->quantity * $this->itemPrice;
$finalPrice = $this->discountedPrice($basePrice); Before basePrice = quantity * itemPrice
seasonalDiscount = self.getSeasonalDiscount()
fees = self.getFees()
finalPrice = discountedPrice(basePrice, seasonalDiscount, fees) After basePrice = quantity * itemPrice
finalPrice = discountedPrice(basePrice) Before let basePrice = quantity * itemPrice;
const seasonDiscount = this.getSeasonalDiscount();
const fees = this.getFees();
const finalPrice = discountedPrice(basePrice, seasonDiscount, fees); After let basePrice = quantity * itemPrice;
let finalPrice = discountedPrice(basePrice);


## Why Refactor

A long list of parameters is hard to understand. In addition, calls to such methods often resemble a series of cascades, with winding and exhilarating value calculations that are hard to navigate yet have to be passed to the method. So if a parameter value can be calculated with the help of a method, do this inside the method itself and get rid of the parameter.


## Benefits

We get rid of unneeded parameters and simplify method calls. Such parameters are often created not for the project as it’s now, but with an eye for future needs that may never come.


## Drawbacks

You may need the parameter tomorrow for other needs... making you rewrite the method.


## How to Refactor

Make sure that the value-getting code doesn’t use parameters from the current method, since they’ll be unavailable from inside another method. If so, moving the code isn’t possible. If the relevant code is more complicated than a single method or function call, use Extract Method to isolate this code in a new method and make the call simple. In the code of the main method, replace all references to the parameter being replaced with calls to the method that gets the value. Use Remove Parameter to eliminate the now-unused parameter.


## Code Examples

### unknown

**Before**
```unknown
int basePrice = quantity * itemPrice;
double seasonDiscount = this.getSeasonalDiscount();
double fees = this.getFees();
double finalPrice = discountedPrice(basePrice, seasonDiscount, fees);
```

**After**
```unknown
int basePrice = quantity * itemPrice;
double finalPrice = discountedPrice(basePrice);
```

### unknown

**Before**
```unknown
int basePrice = quantity * itemPrice;
double seasonDiscount = this.GetSeasonalDiscount();
double fees = this.GetFees();
double finalPrice = DiscountedPrice(basePrice, seasonDiscount, fees);
```

**After**
```unknown
int basePrice = quantity * itemPrice;
double finalPrice = DiscountedPrice(basePrice);
```

### unknown

**Before**
```unknown
$basePrice = $this->quantity * $this->itemPrice;
$seasonDiscount = $this->getSeasonalDiscount();
$fees = $this->getFees();
$finalPrice = $this->discountedPrice($basePrice, $seasonDiscount, $fees);
```

**After**
```unknown
$basePrice = $this->quantity * $this->itemPrice;
$finalPrice = $this->discountedPrice($basePrice);
```

### unknown

**Before**
```unknown
basePrice = quantity * itemPrice
seasonalDiscount = self.getSeasonalDiscount()
fees = self.getFees()
finalPrice = discountedPrice(basePrice, seasonalDiscount, fees)
```

**After**
```unknown
basePrice = quantity * itemPrice
finalPrice = discountedPrice(basePrice)
```

### unknown

**Before**
```unknown
let basePrice = quantity * itemPrice;
const seasonDiscount = this.getSeasonalDiscount();
const fees = this.getFees();
const finalPrice = discountedPrice(basePrice, seasonDiscount, fees);
```

**After**
```unknown
let basePrice = quantity * itemPrice;
let finalPrice = discountedPrice(basePrice);
```
