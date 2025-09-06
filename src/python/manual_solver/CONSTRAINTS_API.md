# Constraints API Reference
Examples of compound expressions:

# Supported Expressions
## Primitives 
### Literal
A literal value (number, string, boolean, etc.)
- Params: Any value
- Returns: The literal value
- Usage: Literal(2), Literal("detective")

### Character
Reference to a specific character by name
- Params: Character name (string)
- Returns: Character position
- Usage: Character("Alice")

## Set generators 
These functions return sets of positions. 

### AllCharacters
Represents all characters in the game
- Params: None
- Returns: Set of all character positions
- Usage: AllCharacters()

### EdgePositions
Get all positions on the edge of the grid
- Params: None
- Returns: Set of edge positions
- Usage: EdgePositions()

### Above
Get all positions above a specific character (same column, lower row numbers)
- Params: Character/Position expression
- Returns: Set of positions
- Usage: Above(Character("Alice"))

### Below
Get all positions below a character (same column, higher row numbers)
- Params: Character/Position expression
- Returns: Set of positions
- Usage: Below(Character("Bob"))

### LeftOf
Get all positions to the left of a character (same row, lower column numbers)
- Params: Character/Position expression
- Returns: Set of positions
- Usage: LeftOf(Character("Charlie"))

### RightOf
Get all positions to the right of a character (same row, higher column numbers)
- Params: Character/Position expression
- Returns: Set of positions
- Usage: RightOf(Character("Eve"))

### Neighbors
Get all neighboring positions (including diagonals) of a character or position
- Params: Character/Position expression
- Returns: Set of neighboring positions
- Usage: Neighbors(Character("Dave"))

## Set operations 
Apply functions to a set of positions to produce a new set.

### Filter
Filter a set of positions by a predicate
- Params: Source set, predicate expression
- Returns: Filtered set of positions
- Usage: Filter(AllCharacters(), HasLabel(Label.INNOCENT))

### Intersection
Intersection of multiple sets
- Params: Multiple set expressions
- Returns: Set intersection
- Usage: Intersection(set1, set2)

### Union
Union of multiple sets
- Params: Multiple set expressions
- Returns: Set union
- Usage: Union(set1, set2, set3)

## Logical operators 
These functions support logical combinations of expressions, evaluating to a boolean.

### And
Logical AND of multiple expressions
- Params: Multiple expressions
- Returns: Boolean evaluation
- Usage: And(expr1, expr2, expr3)

### Not
Logical NOT of an expression
- Params: Single expression
- Returns: Boolean evaluation
- Usage: Not(HasLabel(Label.CRIMINAL))

### Or
Logical OR of multiple expressions
- Params: Multiple expressions
- Returns: Boolean evaluation
- Usage: Or(expr1, expr2, expr3)

## Numerical evaluations
Functions that return a numerical value.

### Count
Count the number of elements in a set
- Params: Set expression
- Returns: Integer count
- Usage: Count(neighbors_of("Alice"))

### Sum
Sum numeric values from a collection
- Params: Collection expression
- Returns: Numeric sum
- Usage: Sum(numeric_collection)

## Predicates
Evaluate truth of a condition on a single position or a set of positions. Can be supplied to Filter.

### HasLabel
Check if a character at a position has a specific label
- Params: Position, Label (INNOCENT or CRIMINAL)
- Returns: Boolean predicate
- Usage: HasLabel(Label.INNOCENT)

### HasProfession
Check if a character at a position has a specific profession
- Params: Profession
- Returns: Boolean predicate
- Usage: HasProfession("detective")

### IsEdge
Check if a position is on the edge of the grid
- Params: None
- Returns: Boolean predicate
- Usage: IsEdge()

### IsUnknown
Check if a character at a position has unknown label
- Params: None
- Returns: Boolean predicate
- Usage: IsUnknown()


## Boolean evaluations
Compare the results of multiple expressions.

### Equal
Check if two expressions evaluate to equal values
- Params: Two expressions
- Returns: Boolean evaluation
- Usage: Equal(count_expr, Literal(2))

### Greater
Check if left expression is greater than right expression
- Params: Two expressions
- Returns: Boolean evaluation
- Usage: Greater(count1, count2)

### GreaterEqual
Check if left expression is greater than or equal to right expression
- Params: Two expressions
- Returns: Boolean evaluation
- Usage: GreaterEqual(count1, count2)

### Less
Check if left expression is less than right expression
- Params: Two expressions
- Returns: Boolean evaluation
- Usage: Less(count1, count2)

### LessEqual
Check if left expression is less than or equal to right expression
- Params: Two expressions
- Returns: Boolean evaluation
- Usage: LessEqual(count1, count2)

### AreConnected
Check if all positions in a set are connected (adjacent to each other)
- Params: Set of positions
- Returns: Boolean evaluation
- Usage: AreConnected(positions)

### IsOdd
Check if a number is odd
- Params: Number
- Returns: Boolean evaluation
- Usage: IsOdd(count)

### IsEven
Check if a number is even
- Params: Number
- Returns: Boolean evaluation
- Usage: IsEven(count)

## Convenience Functions
### above
Get positions above a character
- Compiles to: Above(Character("Alice"))
- Usage: above("Alice")

### below
Get positions below a character
- Compiles to: Below(Character("Bob"))
- Usage: below("Bob")

### count_criminals
Count criminals in an area
- Compiles to: Count(Filter(set_expression, HasLabel(Label.CRIMINAL)))
- Usage: count_criminals(neighbors_of("Alice"))

### count_innocents
Count innocents in an area
- Compiles to: Count(Filter(set_expression, HasLabel(Label.INNOCENT)))
- Usage: count_innocents(neighbors_of("Bob"))

### criminals
Filter for criminals in an area
- Compiles to: Filter(set_expression, HasLabel(Label.CRIMINAL))
- Usage: criminals(AllCharacters())

### innocents
Filter for innocents in an area
- Compiles to: Filter(set_expression, HasLabel(Label.INNOCENT))
- Usage: innocents(neighbors_of("Charlie"))

### left_of
Get positions left of a character
- Compiles to: LeftOf(Character("Charlie"))
- Usage: left_of("Dave")

### neighbors_of
Get neighbors of a character
- Compiles to: Neighbors(Character("Eve"))
- Usage: neighbors_of("Eve")

### right_of
Get positions right of a character
- Compiles to: RightOf(Character("Frank"))
- Usage: right_of("Frank")
