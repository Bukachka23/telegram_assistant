# Code Smells Catalog

Complete taxonomy of all 22 code smells from refactoring.guru, organized by the 5 categories.
Each entry: **Signs → Cause → Treatment → Payoff → When to Ignore**.

Cross-reference: `refactoring_techniques_catalog.md` for technique details | `tips_for_refactoring.md` for Python examples.

---

## 1. Bloaters
> Code, methods, and classes that have grown so large they're hard to work with.
> These smells accumulate gradually over time — nobody notices until it's too late.

---

### Long Method
**Sign:** Method contains too many lines of code. Any method longer than ~10 lines should raise questions.

**Cause:** It's easier to add to an existing method than to create a new one. "Just two more lines" — repeated dozens of times — creates spaghetti. If you feel the need to write a comment inside a method, that code deserves its own named function.

**Treatment:**
- Use **Extract Method** to pull out logical sections
- Local variables block extraction → **Replace Temp with Query**, **Introduce Parameter Object**, or **Preserve Whole Object**
- Extraction still impossible → **Replace Method with Method Object**
- Complex conditionals → **Decompose Conditional**
- Loops → **Extract Method**

> **Python note:** If you feel the need to comment a block inside a method, that block deserves its own named function. See `functions_and_methods.md` → "Keep Functions Small".

**Payoff:** Short methods live longest. They're easier to test, name, understand, and reuse. Long methods are perfect hiding places for duplicate code.

**Performance:** The impact of more method calls is negligible in almost all cases. Clarity always wins.

---

### Large Class
**Sign:** A class contains many fields, methods, or lines of code.

**Cause:** Classes start small and grow. Adding to an existing class feels easier than creating a new one. Nobody removes features, so it only expands.

**Treatment:**
- Part of behavior can become a separate component → **Extract Class**
- Behavior used only in certain cases → **Extract Subclass**
- Need to expose a list of operations for clients → **Extract Interface**
- GUI class with mixed domain logic → **Duplicate Observed Data**

> **Python note:** A class with 10+ methods, or that imports from 5+ unrelated modules, is likely a Large Class. See `when_to_use_classes.md`.

**Payoff:** Reduced cognitive load. Prevents duplication across responsibilities. Splitting large classes avoids scattered code and functionality.

---

### Primitive Obsession
**Sign:**
- Using primitives (`int`, `str`, `float`) instead of small objects (`Currency`, `Range`, `PhoneNumber`)
- Using constants to encode type (e.g., `USER_ADMIN_ROLE = 1`)
- Using string constants as array/dict indices

**Cause:** Primitives are quick to create. Domain types emerge slowly as more fields and validation logic accumulate around them — but developers keep using the raw primitive instead.

**Treatment:**
- Related primitives with behavior → **Replace Data Value with Object**
- Primitive method parameters → **Introduce Parameter Object** or **Preserve Whole Object**
- Type codes driving behavior → **Replace Type Code with Class**, **Replace Type Code with Subclasses**, or **Replace Type Code with State/Strategy**
- Arrays with positional data → **Replace Array with Object**

> **Python note:** Use `@dataclass`, `NamedTuple`, or `Enum` as the primitive replacement. See `data_modeling.md`.

**Payoff:** Flexible, organized code. Validation and formatting logic centralized in the type. No more guessing what that magic number means.

---

### Long Parameter List
**Sign:** More than 3–4 parameters for a method.

**Cause:** Multiple algorithms merged into one method; or excessive decoupling where all needed data is passed explicitly instead of passing the object.

**Treatment:**
- Parameters come from another object's method calls → **Replace Parameter with Method Call**
- Parameters all come from one object → **Preserve Whole Object**
- Parameters come from different sources → **Introduce Parameter Object**

> **Python note:** Use `*` to enforce keyword-only args for optional flags. Use `@dataclass` as parameter objects. See `tips_for_refactoring.md` → "Use Keyword-Only Arguments For Optional Flags".

**Payoff:** Shorter, more readable call sites. Often reveals hidden duplication.

**When to Ignore:** Don't remove parameters if doing so creates an unwanted dependency between classes.

---

### Data Clumps
**Sign:** The same group of variables (e.g., `host`, `port`, `user`, `password`) appears repeatedly across the codebase — in class fields and method parameters.

**Cause:** Poor program structure or copy-paste programming. Detection test: delete one variable from the group — if the others stop making sense, the group belongs together as a class.

**Treatment:**
- Fields clumping in a class → **Extract Class**
- Parameter clumps in method signatures → **Introduce Parameter Object**
- Pass the whole group at once → **Preserve Whole Object**
- Code that uses this data → move it into the new class

> **Python note:** `@dataclass` or `NamedTuple` are ideal for parameter objects. See `data_modeling.md`.

**Payoff:** Reduces code size. Related operations can now live in the new class. Fewer scattered edits when the group changes.

**When to Ignore:** Passing a whole object rather than primitives may create unwanted coupling if the caller shouldn't know about the object.

---

## 2. Change Preventers
> These smells mean that changing one thing forces changes in many other places.
> Program evolution becomes expensive, risky, and slow.

---

### Divergent Change
**Sign:** You find yourself changing many *unrelated* methods every time you modify a class. Example: adding a new product type requires changing find, display, and order methods — all in the same class.

**Cause:** Poor program structure or copy-paste programming mixed multiple responsibilities into one class. **Opposite of Shotgun Surgery** — one class absorbs many unrelated changes.

**Treatment:**
- Split the class by responsibility → **Extract Class**
- If classes share behavior → **Extract Superclass** or **Extract Subclass**

**Payoff:** Organized code. Reduced duplication. Each class has one reason to change.

---

### Parallel Inheritance Hierarchies
**Sign:** Every time you create a subclass for `ClassA`, you find yourself also needing to create a subclass for `ClassB`.

**Cause:** Small hierarchies grew in parallel over time; the coupling between them wasn't noticed early enough.

**Treatment:**
1. Make instances of one hierarchy reference instances of the other
2. Use **Move Method** and **Move Field** to consolidate the hierarchy into one

**Payoff:** Reduced duplication. Better code organization.

**When to Ignore:** Sometimes parallel hierarchies are the lesser evil. If de-duplication makes things more complex, revert and accept the duplication.

---

### Shotgun Surgery
**Sign:** A single conceptual change requires many small edits scattered across multiple classes.

**Cause:** One responsibility has been spread across many classes — often the over-eager result of fixing a Divergent Change. **Opposite of Divergent Change** — one change, many classes.

**Treatment:**
- Use **Move Method** and **Move Field** to consolidate responsibility into one class
- If original classes become empty shells after consolidation → **Inline Class**

**Payoff:** Better organization. Less duplication. Easier maintenance. One change = one place.

---

## 3. Dispensables
> These are pointless, unneeded elements whose removal makes the code cleaner, shorter, and easier to understand.

---

### Comments
**Sign:** A method is filled with explanatory comments that describe *what* the code does (not *why*).

**Cause:** Comments appear when code isn't self-explanatory. They become a "deodorant" masking code that should be refactored instead. A comment that explains *what* a block does is a sign the block should be extracted and named.

**Treatment:**
- Complex expression → **Extract Variable** with a descriptive name
- Commented code section → **Extract Method** (use the comment as the method name)
- Method still needs explanation → **Rename Method**
- Asserting a required state → **Introduce Assertion**

**Payoff:** Code becomes self-documenting. The "why" can still be a comment; the "what" should be in the name.

**When to Ignore:**
- Explaining *why* a particular approach was chosen
- Complex algorithms where all simplification options are exhausted
- Public API docstrings are always valuable

---

### Duplicate Code
**Sign:** Two or more code fragments look almost identical.

**Cause:** Multiple programmers working independently; "almost right" copy-paste under deadline pressure; intentional shortcuts that were never cleaned up.

**Treatment:**
| Situation | Technique |
|-----------|-----------|
| Same code in two methods of the same class | **Extract Method**, call from both |
| Same code in sibling subclasses | **Extract Method** → **Pull Up Method** (+ **Pull Up Field** if needed) |
| Duplicate in constructors | **Pull Up Constructor Body** |
| Similar but not identical | **Form Template Method** |
| Same result, different algorithm | **Substitute Algorithm** |
| Duplicate in unrelated classes | **Extract Superclass** or **Extract Class** + compose |
| Same code in all branches | **Consolidate Duplicate Conditional Fragments** |
| Many similar conditionals → same result | **Consolidate Conditional Expression** → **Extract Method** |

**Payoff:** Shorter, simpler structure. Less maintenance. Fewer bugs (one fix instead of many).

**When to Ignore:** In very rare cases, merging duplicates actually reduces clarity (e.g., coincidentally similar logic that will diverge).

---

### Lazy Class
**Sign:** A class doesn't do enough to justify its existence. Maintaining it costs more than it's worth.

**Cause:** A once-meaningful class reduced by refactoring, or a class created speculatively for future features that never arrived.

**Treatment:**
- Useless class → **Inline Class**
- Near-empty subclass → **Collapse Hierarchy**

**Payoff:** Reduced code size. Fewer files to navigate. Easier maintenance.

**When to Ignore:** A Lazy Class can serve as a named placeholder for intended future development. Maintain balance between clarity and simplicity.

---

### Data Class
**Sign:** A class contains only fields and crude getters/setters. It's a pure data container with no behavior of its own.

**Cause:** Newly created classes start this way legitimately. The smell is when they *stay* this way while the behavior that operates on them is scattered in client code.

**Treatment:**
1. Public fields → **Encapsulate Field** (add getters/setters)
2. Exposed collection fields → **Encapsulate Collection**
3. Find behavior in client code that belongs in this class → **Move Method** / **Extract Method**
4. After adding real behavior → **Remove Setting Method** and **Hide Method** to tighten access

> **Python note:** A `@dataclass` used as a DTO/value object is *intentionally* a data class and is not a smell. The smell is when behavior that naturally belongs to the data (validation, formatting, business rules) lives scattered in callers.

**Payoff:** Operations on data centralized in one place. Client duplication reduced. Better cohesion.

---

### Dead Code
**Sign:** A variable, parameter, field, method, or class is no longer used (usually because requirements changed).

**Cause:** Requirements evolved or corrections were made, but nobody cleaned up the old code. Also common in unreachable conditional branches.

**Treatment:**
- Delete unused code and files directly
- Unnecessary class → **Inline Class** or **Collapse Hierarchy**
- Unused parameters → **Remove Parameter**

> **Python note:** Use `ruff` (rules `F401`, `F811`) or `vulture` to detect dead code automatically.

**Payoff:** Reduced code size. Simpler maintenance. Less confusion about what's actually used.

---

### Speculative Generality
**Sign:** Unused classes, methods, fields, or parameters exist because they were created "just in case" for future features that never materialized.

**Cause:** Over-engineering — building for anticipated flexibility before it's needed (YAGNI violation).

**Treatment:**
- Unused abstract classes → **Collapse Hierarchy**
- Unnecessary delegation layers → **Inline Class**
- Unused methods → **Inline Method**
- Methods with unused parameters → **Remove Parameter**
- Unused fields → delete them

**Payoff:** Slimmer, simpler code. Less noise. Easier to understand the actual system.

**When to Ignore:**
- Framework code where the functionality is needed by framework users, not the framework itself
- Elements only referenced from unit tests (they serve a testing purpose)

---

## 4. Object-Orientation Abusers
> Incomplete or incorrect application of object-oriented programming principles.

---

### Switch Statements
**Sign:** Complex `switch`/`match` operator or long chain of `if/elif` blocks that dispatches based on object type or mode.

**Cause:** Type-based dispatch scattered across the codebase. When a new type is added, every switch site must be found and updated.

**Treatment:**
1. Move the switch to the right class: **Extract Method** → **Move Method**
2. Switch on type code → **Replace Type Code with Subclasses** or **Replace Type Code with State/Strategy**
3. Apply **Replace Conditional with Polymorphism**
4. Conditions call the same method with different params → **Replace Parameter with Explicit Methods**
5. One branch is `None` → **Introduce Null Object**

> **Python note:** Python's `match` (3.10+) is not inherently a smell. The smell is type-based dispatch *spread across the codebase* rather than centralized behind polymorphism. See `clean_architecture.md` → Open/Closed Principle.

**Payoff:** Better code organization. Adding a new type no longer requires hunting down every switch site.

**When to Ignore:** Simple switch with straightforward actions. Factory patterns legitimately use type dispatch to select which class to create.

---

### Temporary Field
**Sign:** An object has fields that are set and used only in specific circumstances — they're `None` or empty most of the time.

**Cause:** A developer created class-level fields to avoid passing many parameters to a complex algorithm, but those fields have no meaning outside that algorithm.

**Treatment:**
- Move temporary fields and their algorithm to a new class → **Extract Class** (creating a Method Object)
- Replace `None`-checks on temporary fields → **Introduce Null Object**

**Payoff:** Better code clarity and organization. Fields always mean something.

---

### Refused Bequest
**Sign:** A subclass uses only some of the inherited methods/properties. Unused inherited methods go unused or are overridden to raise exceptions (`NotImplementedError`).

**Cause:** Inheritance was used for code reuse only, not because a true IS-A relationship exists. The subclass isn't really a specialization of the superclass.

**Treatment:**
- No true IS-A relationship → **Replace Inheritance with Delegation** (store superclass as a field)
- True IS-A but wrong split → **Extract Superclass** (create a new superclass with only what both classes truly share)

**Payoff:** Cleaner hierarchy. No surprising inherited behavior. No `NotImplementedError` surprises.

---

### Alternative Classes with Different Interfaces
**Sign:** Two classes perform the same function but have different method names (e.g., `UserFetcher.fetch()` and `UserLoader.load()` do the same thing).

**Cause:** One developer created a class without knowing an equivalent already existed.

**Treatment:**
1. **Rename Method** to harmonize signatures across classes
2. **Move Method**, **Add Parameter**, **Parameterize Method** to align implementations
3. If only partially duplicate → **Extract Superclass**
4. Delete the redundant class if possible

**Payoff:** Eliminates unnecessary duplication. Clearer codebase — one clear way to do each thing.

**When to Ignore:** When alternative classes come from different libraries you can't modify.

---

## 5. Couplers
> Smells that contribute to excessive coupling between classes, or result from replacing coupling with excessive delegation.

---

### Feature Envy
**Sign:** A method accesses data of another object more than its own object's data.

**Cause:** Can arise after fields are moved to a data class without also moving the operations that use them.

**Treatment:**
- Entire method belongs elsewhere → **Move Method**
- Part of a method belongs elsewhere → **Extract Method** first, then **Move Method**
- Method uses data from several classes → move it to the class that contains the most data it uses

> **Python note:** See `tips_for_refactoring.md` → "Feature Envy" and "Move Method".

**Payoff:** Reduced duplication. Better organization — behavior lives with the data it operates on.

**When to Ignore:** Intentionally separate strategies (Strategy, Visitor patterns) keep behavior deliberately separate from data.

---

### Inappropriate Intimacy
**Sign:** One class accesses the private fields and internal methods of another class directly.

**Cause:** Classes become overly entangled over time, especially through bidirectional associations or inheritance shortcuts.

**Treatment:**
- Move the accessed parts → **Move Method** and **Move Field**
- Formalize the relationship → **Extract Class** + **Hide Delegate**
- Mutual dependency → **Change Bidirectional Association to Unidirectional**
- Subclass accessing superclass internals → **Replace Delegation with Inheritance** (if IS-A holds)

**Payoff:** Better organization. Simpler support. Classes are easier to reuse independently.

---

### Incomplete Library Class
**Sign:** A library you depend on doesn't provide a method you need, and you can't modify the library directly.

**Cause:** Library authors haven't implemented what you need, or the library is read-only.

**Treatment:**
- Need just a few extra methods → **Introduce Foreign Method** (add the method to a client class, pass the library object as an argument)
- Need significant additions → **Introduce Local Extension** (subclass or wrapper around the library class)

> **Python note:** In Python, prefer composition (a thin wrapper class) over subclassing third-party classes.

**Payoff:** Avoids reimplementing library functionality from scratch. Keeps extensions localized.

**When to Ignore:** Extensions add their own maintenance burden. Weigh cost vs. benefit.

---

### Message Chains
**Sign:** Code chains calls like `a.get_b().get_c().get_d()`.

**Cause:** The client depends on knowing the entire navigation path through the object graph. Any structural change breaks the chain.

**Treatment:**
- **Hide Delegate**: Add a method to the first object that handles the navigation internally
- If the end object's purpose is clear → **Extract Method** + **Move Method** to pull the logic closer to the start

> **Python note:** Django ORM chaining (`queryset.filter().exclude().order_by()`) is intentional fluent API, not a smell. This applies to domain object navigation chains.

**Payoff:** Reduces inter-class dependencies. Less brittle, more refactor-friendly code.

**When to Ignore:** Overly aggressive delegate hiding can cause the Middle Man smell — balance is needed.

---

### Middle Man
**Sign:** A class's only purpose is to delegate calls to another class. It does no real work itself.

**Cause:** Over-zealous elimination of Message Chains; gradual migration of a class's responsibilities elsewhere, leaving an empty shell that still delegates.

**Treatment:**
- **Remove Middle Man**: Delete the delegation methods and let clients call the target class directly

**Payoff:** Less indirection. Leaner, more direct code.

**When to Ignore:**
- Intentional indirection for decoupling (Proxy, Decorator patterns)
- The middle man was purposefully added to prevent inter-class dependencies

---

## Quick Reference: Smell → Primary Technique

| Smell | Category | Primary Fix |
|-------|----------|-------------|
| Long Method | Bloater | Extract Method, Decompose Conditional |
| Large Class | Bloater | Extract Class, Extract Subclass |
| Primitive Obsession | Bloater | Replace Data Value with Object, Introduce Parameter Object |
| Long Parameter List | Bloater | Introduce Parameter Object, Preserve Whole Object |
| Data Clumps | Bloater | Extract Class, Introduce Parameter Object |
| Divergent Change | Change Preventer | Extract Class |
| Parallel Inheritance | Change Preventer | Move Method + Move Field |
| Shotgun Surgery | Change Preventer | Move Method + Move Field, Inline Class |
| Comments | Dispensable | Extract Method, Rename Method, Extract Variable |
| Duplicate Code | Dispensable | Extract Method, Pull Up Method, Form Template Method |
| Lazy Class | Dispensable | Inline Class, Collapse Hierarchy |
| Data Class | Dispensable | Encapsulate Field, Move Method |
| Dead Code | Dispensable | Delete, Remove Parameter |
| Speculative Generality | Dispensable | Collapse Hierarchy, Inline Method, Remove Parameter |
| Switch Statements | OO Abuser | Replace Conditional with Polymorphism |
| Temporary Field | OO Abuser | Extract Class, Introduce Null Object |
| Refused Bequest | OO Abuser | Replace Inheritance with Delegation |
| Alternative Classes | OO Abuser | Rename Method, Extract Superclass |
| Feature Envy | Coupler | Move Method, Extract Method |
| Inappropriate Intimacy | Coupler | Move Method, Move Field |
| Incomplete Library Class | Other | Introduce Foreign Method, Introduce Local Extension |
| Message Chains | Coupler | Hide Delegate |
| Middle Man | Coupler | Remove Middle Man |
