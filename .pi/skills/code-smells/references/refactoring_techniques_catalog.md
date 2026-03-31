# Refactoring Techniques Catalog

Quick-reference lookup for all ~65 refactoring techniques from refactoring.guru, organized by category.
Format: **Problem → Solution** with Python notes where applicable.

Cross-reference: `code_smells_catalog.md` for smell → technique mappings | `tips_for_refactoring.md` for Python code examples.

---

## 1. Composing Methods
> Most refactoring is about correctly composing methods.
> Excessively long methods are the root of most quality problems — they conceal logic and hide duplication.

| Technique | Problem | Solution | Python Note |
|-----------|---------|----------|-------------|
| **Extract Method** | A code fragment can be grouped logically | Move the fragment to a new named method; replace original with a call | If you feel the need to comment a block, extract it instead |
| **Inline Method** | A method body is more obvious than the method's name | Replace all call sites with the body; delete the method | Use when a method is just a one-liner wrapper with no added clarity |
| **Extract Variable** | An expression is hard to understand | Assign parts of the expression to descriptively-named intermediate variables | Use to eliminate a "what does this do?" comment above a complex condition |
| **Inline Temp** | A temp variable holds the result of a simple expression and nothing else | Replace all uses of the variable with the expression directly | When the variable adds no clarity or is used only once |
| **Replace Temp with Query** | A local variable stores a computed result for later use | Move the computation to a new method; call the method wherever needed | Enables Extract Method on methods that reference the temp |
| **Split Temporary Variable** | One variable is reused for multiple unrelated intermediate values | Create separate variables for each distinct purpose | Python: single-assignment variables (`a: int = compute()`) are easier to reason about |
| **Remove Assignments to Parameters** | The method body reassigns a value to a parameter | Use a local variable instead of mutating the parameter | Python passes by object reference; reassigning a parameter name surprises callers |
| **Replace Method with Method Object** | Long method can't be extracted because local variables are too intertwined | Move the method to a new class; local variables become instance fields; split into sub-methods | Python: `class OrderCalculator: def execute(self) -> Result` |
| **Substitute Algorithm** | The existing algorithm needs to be replaced with a better one | Replace the method body with the new algorithm entirely | Ensure all tests pass before and after the swap |

---

## 2. Moving Features Between Objects
> Even if functionality was distributed poorly, you can safely reorganize it.
> These techniques move behavior, fields, and responsibilities to where they belong.

| Technique | Problem | Solution | Python Note |
|-----------|---------|----------|-------------|
| **Move Method** | A method is used more in another class than in its own | Create the method in the target class; redirect or remove the original | See `tips_for_refactoring.md` → "Move Method" |
| **Move Field** | A field is used more in another class than in its own | Create the field in the target class; redirect all users | See `tips_for_refactoring.md` → "Move Field" |
| **Extract Class** | One class does the work of two classes | Create a new class; move the relevant fields and methods into it | See `tips_for_refactoring.md` → "Extract Class" |
| **Inline Class** | A class does almost nothing and isn't expected to grow | Move all its features into another class; delete the empty shell | See `tips_for_refactoring.md` → "Inline Class" |
| **Hide Delegate** | A client gets `B` from `A` and calls methods on `B` directly (`a.getB().doC()`) | Add a method on `A` that delegates to `B`; client only knows `A` | Reduces client knowledge of the internal object graph |
| **Remove Middle Man** | A class has too many methods that simply delegate to another object | Delete the delegation methods; let clients call the target directly | Use when delegation adds no value — see Middle Man smell |
| **Introduce Foreign Method** | A utility/library class lacks a method you need; you can't modify it | Add the method to a client class, passing the library object as an argument | Python: standalone function or `@staticmethod` in the client class |
| **Introduce Local Extension** | A library class needs significant additions; you can't modify it | Create a subclass or wrapper with the additional methods | Python: prefer a composition wrapper over subclassing 3rd-party classes |

---

## 3. Organizing Data
> Replace primitives with richer class functionality.
> Untangle class associations to make classes more portable and reusable.

| Technique | Problem | Solution | Python Note |
|-----------|---------|----------|-------------|
| **Self Encapsulate Field** | Private fields are accessed directly inside the class | Create a getter/setter; access the field only through them | Python: use `@property` for controlled access |
| **Replace Data Value with Object** | A simple data field grows its own behavior and related data | Create a class for the field; store the object in the original class | See `tips_for_refactoring.md` → "Replace Data Value With Object" |
| **Change Value to Reference** | Many identical instances of a class exist where a single shared object would do | Convert to a single reference object (e.g., a shared registry or cache) | Use with care — shared mutable state adds complexity |
| **Change Reference to Value** | A reference object is tiny, infrequently changed, and lifecycle overhead isn't worth it | Convert to an immutable value object | Python: use `@dataclass(frozen=True)` |
| **Replace Array with Object** | An array/list holds heterogeneous data accessed by position index | Replace with an object that has named fields for each element | Python: use `@dataclass` or `NamedTuple` |
| **Duplicate Observed Data** | Domain data is stored in a GUI/presentation class | Separate the domain data into its own class; synchronize with the GUI class | Applies when mixing UI code and business logic |
| **Change Unidirectional to Bidirectional** | Two classes need each other's features but the association is one-way only | Add the reverse association to the class that needs it | Add carefully — bidirectional associations add coupling |
| **Change Bidirectional to Unidirectional** | A bidirectional association exists but one side doesn't use the other | Remove the unused direction | Prefer unidirectional whenever possible |
| **Encapsulate Field** | A field is `public` | Make the field private; add getter and setter methods | Python: use `@property`; avoid trivial getters for internal data that doesn't need validation |
| **Encapsulate Collection** | A class exposes a mutable collection directly via a getter | Make the getter return a read-only view; add explicit add/remove methods | Python: return `tuple()` copy or use `@property` with a defensive copy |
| **Replace Magic Number with Symbolic Constant** | Code uses a number whose meaning isn't obvious from context | Replace with a named constant | Python: module-level constant (`MAX_RETRIES = 3`) or `Enum` |
| **Replace Type Code with Class** | A class has a type-code field that does NOT drive conditional behavior | Create a class for the type; use its objects as the field type | Python: `Enum` class |
| **Replace Type Code with Subclasses** | A type code directly drives behavior (triggers conditionals) | Create subclasses for each type value; move behavior into them | Useful when each type has meaningfully different behavior |
| **Replace Type Code with State/Strategy** | A type code drives behavior but subclassing is impossible (mutable type or final class) | Replace type code with a state/strategy object that can be swapped at runtime | See `design_patterns.md` → Strategy Pattern |
| **Replace Subclass with Fields** | Subclasses differ only in methods that return constant values | Replace those methods with fields in the parent class; delete the subclasses | Simplifies hierarchy when there's no real behavioral difference |

---

## 4. Simplifying Conditional Expressions
> Conditionals grow increasingly complex over time.
> Fight them systematically to keep control flow readable.

| Technique | Problem | Solution | Python Note |
|-----------|---------|----------|-------------|
| **Decompose Conditional** | A complex `if/elif/else` or `match` has complicated logic | Extract the condition, then-branch, and else-branch into named methods | Makes control flow read like prose: `if is_summer_rate(): apply_summer_pricing()` |
| **Consolidate Conditional Expression** | Multiple separate conditions all lead to the same result or action | Merge them into a single combined expression; extract to a named method | Clarifies that the conditions share a single purpose |
| **Consolidate Duplicate Conditional Fragments** | The same code appears in every branch of a conditional | Move the duplicated code outside of the conditional | DRY inside conditional blocks |
| **Remove Control Flag** | A boolean variable acts as a control flag across multiple conditions and loops | Replace with `break`, `continue`, or `return` | Flattens complex loop/condition structures |
| **Replace Nested Conditional with Guard Clauses** | Deeply nested conditionals make the normal execution path hard to follow | Extract edge cases and error conditions as early returns at the top of the function | See `functions_and_methods.md` → "Guard Clauses" |
| **Replace Conditional with Polymorphism** | A conditional dispatches different actions based on object type or mode | Create subclasses or Strategy objects; move each branch into an override | See `clean_architecture.md` → Open/Closed Principle; `design_patterns.md` → Strategy |
| **Introduce Null Object** | Many `None`/null checks are scattered in client code | Return a Null Object that implements the expected interface with safe default behavior | Python: define a `NullXxx` class with no-op methods; or use sentinel objects |
| **Introduce Assertion** | A section of code implicitly assumes certain preconditions are always true | Make the assumption explicit with `assert` statements | Use `assert` for internal invariants; raise specific exceptions for public API validation |

---

## 5. Simplifying Method Calls
> Make method signatures simpler, cleaner, and more self-documenting.
> This simplifies the interfaces between classes.

| Technique | Problem | Solution | Python Note |
|-----------|---------|----------|-------------|
| **Rename Method** | A method's name doesn't clearly describe what it does | Rename it to something descriptive | Highest ROI refactoring — naming is free and always improves readability |
| **Add Parameter** | A method doesn't have enough data to perform correctly | Add a new parameter to pass the missing data | Use keyword-only args (`*`) when adding optional parameters |
| **Remove Parameter** | A parameter is never used in the method body | Remove the unused parameter | Check subclass overrides before removing; update all call sites |
| **Separate Query from Modifier** | A method both returns a value and changes object state | Split into two methods: one queries (pure), one modifies (no return) | Command-Query Separation (CQS) principle — see `tips_for_refactoring.md` |
| **Parameterize Method** | Multiple methods perform the same logic but with different hardcoded values | Merge into one method with a parameter for the varying value | Don't over-parameterize — if behavior diverges, keep them separate |
| **Replace Parameter with Explicit Methods** | A method switches its entire behavior based on a single parameter value | Split into separate named methods for each case | Better API clarity; see `tips_for_refactoring.md` → "Avoid Boolean Blindness" |
| **Preserve Whole Object** | Multiple values are extracted from one object and passed as separate parameters | Pass the whole object instead | Simpler signature; creates a dependency on the passed object type |
| **Introduce Parameter Object** | The same group of parameters appears repeatedly across multiple method signatures | Replace the parameter group with a single parameter object (class/dataclass) | Python: use `@dataclass`; see `data_modeling.md` |
| **Remove Setting Method** | A field should only be set during construction and must never change after that | Remove the setter method entirely | Python: `@dataclass(frozen=True)` or private field with no setter |
| **Hide Method** | A method is not used outside its own class or class hierarchy | Make the method private or protected | Python: prefix with `_` (convention) or `__` (name mangling for true private) |
| **Replace Constructor with Factory Method** | A constructor is complex, or needs to return different types/subclasses | Create a factory classmethod; replace direct constructor calls | Python: `@classmethod` factory — `User.from_dict(data)`, `Payment.for_stripe(...)` |
| **Replace Error Code with Exception** | A method returns a special value (e.g., `-1`, `None`, `False`) to signal an error | Raise an exception instead | Python idiomatic pattern: exceptions > return codes. See `tips_for_refactoring.md` |
| **Replace Exception with Test** | An exception is thrown where a simple conditional check would be cleaner | Replace the `try/except` with a pre-condition check | Use exceptions for truly exceptional cases; use `if` for expected states |

---

## 6. Dealing with Generalization
> Techniques for moving functionality along the inheritance hierarchy,
> creating new classes and interfaces, and replacing inheritance with delegation.

| Technique | Problem | Solution | Python Note |
|-----------|---------|----------|-------------|
| **Pull Up Field** | Two subclasses have the same field | Remove from subclasses; move to the superclass | Eliminates hierarchy duplication |
| **Pull Up Method** | Subclasses have methods that perform the same work | Make the methods identical; move to the superclass | Use ABCs (`abc.ABC`) or `Protocol` for the interface |
| **Pull Up Constructor Body** | Subclass `__init__` methods have mostly identical code | Create a superclass `__init__`; call `super().__init__()` in subclasses | Standard Python OOP |
| **Push Down Method** | A superclass method is only used by one (or a few) subclasses | Move the method to the relevant subclass(es) | Inverse of Pull Up Method |
| **Push Down Field** | A field is only used by some subclasses | Move the field to those subclasses | Inverse of Pull Up Field |
| **Extract Subclass** | A class has features that are used only in specific cases | Create a subclass and use it for those special cases | Consider using composition if the cases are orthogonal |
| **Extract Superclass** | Two classes share common fields and methods | Create a shared superclass; move common elements into it | Python: also consider `Protocol` for structural typing instead of forcing inheritance |
| **Extract Interface** | Multiple clients use the same subset of a class's interface, or two classes share part of their interface | Extract that shared subset into its own interface/protocol | Python: use `Protocol` (structural subtyping — no inheritance required) |
| **Collapse Hierarchy** | A subclass is practically identical to its superclass | Merge subclass and superclass into one | Remove empty or near-empty subclasses aggressively |
| **Form Template Method** | Subclasses implement algorithms that have the same structure and sequence of steps | Define the algorithm skeleton in the superclass; defer the varying steps to subclasses | Classic Template Method pattern |
| **Replace Inheritance with Delegation** | A subclass uses only part of superclass methods; or the IS-A relationship is false | Use composition: store the old superclass as a field; delegate specific calls to it | Python: prefer composition generally — see `when_to_use_classes.md` |
| **Replace Delegation with Inheritance** | A class has many simple methods that just delegate to all methods of another class | Make the class inherit from the delegate (only if a true IS-A relationship exists) | Inverse of Replace Inheritance with Delegation — use rarely |

---

## Quick Lookup: Symptom → Technique

| What you see in the code | Technique to apply |
|--------------------------|-------------------|
| Method is too long | Extract Method |
| Expression is confusing | Extract Variable |
| Variable used for two things | Split Temporary Variable |
| Method can't be extracted (tangled locals) | Replace Method with Method Object |
| Method clearly belongs in another class | Move Method |
| Class is doing too much | Extract Class |
| Class does almost nothing | Inline Class |
| Chain: `a.b().c().d()` | Hide Delegate |
| Class only delegates, no real work | Remove Middle Man |
| Repeated group of parameters | Introduce Parameter Object |
| Pass several values from one object | Preserve Whole Object |
| Many `None` checks everywhere | Introduce Null Object |
| Complex `if/elif` dispatching on type | Replace Conditional with Polymorphism |
| Nested conditions, hard to see normal flow | Replace Nested Conditional with Guard Clauses |
| Multiple conditions, same outcome | Consolidate Conditional Expression |
| Method returns error code | Replace Error Code with Exception |
| Constructor is overly complex | Replace Constructor with Factory Method |
| Field should only be set at init | Remove Setting Method |
| Two subclasses share fields/methods | Pull Up Field / Pull Up Method |
| Subclass barely uses superclass | Replace Inheritance with Delegation |
| Type code drives `if/elif` branches | Replace Type Code with Subclasses / State-Strategy |
| Magic number in code | Replace Magic Number with Symbolic Constant |
| Public mutable field | Encapsulate Field |
