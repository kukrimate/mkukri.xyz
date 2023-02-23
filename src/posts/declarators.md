<!--GEN_META
GEN_TITLE=Techniques for parsing C declarators
GEN_DESCRIPTION=
GEN_KEYWORDS=
GEN_AUTHOR=Máté Kukri
GEN_TIMESTAMP=2022-05-01 20:01
GEN_COPYRIGHT=Copyright (C) Máté Kukri, 2022
-->

## 1. Representation of types

Compiler writers need a programmatic representation of types in the source
program for both deciphering the semantics of some operators, and type checking
to aid the programmer. The most obvious data structure for this purpose is a
discriminated union.

To construct such type objects, each variant's constructor takes its member
type(s) as parameters. Each constructor can also check them for semantic
correctness, and return either the constructed object, or an error.
For example, if we want to enforce a C like rule that functions cannot return
or take as parameters arrays, or other functions, the constructor for the
function variant would have to check this.

If we consider a simple programming language with integers,
pointers, arrays, and functions, our data structure will look like:

```
Type = Void                     ; Return type of procedures
     | Integer                  ; Integer value
     | Pointer {                ; Pointer to value with base_type
        base_type: Type
     }
     | Array {                  ; Array of elem_count values with elem_type
        elem_type: Type,
        elem_count: int,
     }
     | Function {               ; Function of param_types to return_type
        return_type: Type,
        param_types: [Type],
     }
     ;
```

## 2. The academic's reality

Obviously source programs start their life as text written by the programmer,
thus we somehow need to turn syntax into a sequence of calls to the constructors
described above.

Some programming languages such as Rust have a straightforward syntax for
declaring types. For example, a Rust-like syntax for the simple type system
above can be described by the grammar below.

Writing a parser that constructs such a data structure from the grammar above
is trivial. For instance using an LR parser generator the semantic action for
each rule is just a call to the constructor of the variant in question.


```
<type>      ::= int                             => Type::Integer
              | * <type>                        => Type::Pointer($2)
              | [ <type> ; <expr> ]             => Type::Array($2, $4)
              | fn ( <type-list>? )             => Type::Function($3, Type::Void)
              | fn ( <type-list>? ) -> <type>   => Type::Function($3, $6)

<type-list> ::= <type>
              | <type-list> , <type>
```

## 3. C: Syntax from 1969

As it turns out, the vague "some programming" languages above didn't include C,
one of the most popular programming language in the world. Instead, in C, types
are declared together with a name using a structure called a declarator. The
idea behind this is that the declaration of a variable matches exactly what
the programmer can do with it.

The unary prefix operator `*` is used to de-reference a pointer, the postfix
operators `[]` and `()` are used for arrays accesses and function calls.
The postfix operators in C have the higher precedence and they associate
left-to-right, prefix associate right-to-left. Parenthesis can be used to
override precedence in both cases. Following these rules results in the grammar
below:

```
<pri-expr>  ::= ( <expr> )
              | IDENTIFIER
              | <pri-expr> [ <expr> ]
              | <pri-expr> ( <expr-list> )

<sec-expr>  ::= <pri-expr>
              | "*" <sec-expr>

...
```

Declarations follow essentially the same syntax, the only difference is they
are introduced by keywords known as "type specifiers". These words specify the
"base type" (my term, not in ISO/IEC 9899) of the declarator(s) to follow. The
base type will become the `base_type` of any pointer declarators that follow,
the `elem_type` of any array declarators, and so on. For the purpose of this
discussion we assume a declaration is introduced by one of the words `int`
or `void`, and each declaration only contains one declarator. Using these
assumptions, we end up with the following grammar:

```

<declaration>    ::= <type-specifier> <declarator>

<type-specifier> ::= int
                   | void

<pri-decl>       ::= ( <declarator> )
                   | IDENTIFIER
                   | <pri-decl> [ <expr> ]
                   | <pri-decl> ( <declaration-list> )

<declarator>     ::= <pri-decl>
                   | "*" <declarator>

...
```

Coming up with the grammar was a reasonably easy task, the problem is that this
grammar above cannot be easily annotated with semantic actions that produce the
data structure in the first section. Parsers using the grammar above will walk
the declarator "inside-out". In each reduction we have as an operand the type
whose constructor should take the type just to be constructed as an arguement.
To create the data structure we need to fold the declarator "back-in". The
following sections will introduce four approaches to accomplish this.

## 4. Clean solution in two passes

First we will explore a solution that leads directly from the grammar above.
Instead of trying to construct types while parsing, we introduce the data type
below to temporarily represent a declarator after parsing. This can be
constructed trivially using semantic actions attached to our grammar.

The semantic value of a `<declarator>` will be a linked list of declarators
in precedence order, and re-associated left-to-right. Then in the action code
for `<declaration>` we can combine the list with the type specifiers to derive
the final type and name of the declaration. For example, the declaration
`int *(*my_array)[5][6]` and will result in the linked-list `*[6][5]*my_array`.
Then after combination with the type specifiers, will lead to the type
(in the notation from section 2) `*[[*int; 6]; 5]`.

The algorithm that accomplished this is described below. It takes
the type specifiers to be the first element, then just walks the list.
On each element we take the type constructed for the previous element,
and the values from the object to construct the next type:

```
Decl = Name     { name: String }
     | Pointer  { next: Decl }
     | Array    { next: Decl, elem_count: int }
     | Function { next: Decl, param_types: [Type] }
     ;

<declaration>    ::= <type-specifier> <declarator>      => f($1, $2)

<pri-decl>       ::= ( <declarator> )                   => $2
                   | IDENTIFIER                         => Decl::Name($1)
                   | <pri-decl> [ <expr> ]              => Decl::Array($1, $3)
                   | <pri-decl> ( <declaration-list> )  => Decl::Function($1, $3)

<declarator>     ::= <pri-decl>                         => $1
                   | "*" <declarator>                   => Decl::Pointer($2)

f (Type, Decl)
    [prev, Name { name }]                  (prev, name)
    [prev, Pointer { next }]               f(Type::Pointer(prev), next)
    [prev, Array { next, elem_count }]     f(Type::Array(prev, elem_count), next)
    [prev, Function { next, param_types }] f(Type::Function(prev, param_types), next)
```

The reason this method is being referred to as "The Good" is because it can be
implemented using immutable data structures, and leaves our easy to understand
method for constructing type objects unchanged. The downside is that it allocates
extra memory, and takes two passes over each declarator to arrive at the type.
In practice, this is not an issue on modern computers for a language as simple
as C, for example the Plan 9 C compiler uses this method.

## 5. Hacking our way to a single pass

The second approach re-works the grammar in an attempt to parse the declarators
in a more natural order required for type construction. Using this strategy we
will be able to parse declarators in one pass, and do constructor calls in most
places to construct types.
However it leads to a chicken-and-egg problem with parenthesised declarators
that we will only be able to resolve by either breaking away from traditional
left-to-right parsing, or by deviating from the value based ownership model of
our recursive structures, and acknowledging their true, reference based nature.

First, ignoring parenthesised declarators, it's reasonably easy to construct
the grammar below that parses declarations in our desired order. The arguments
to the constructor calls for the suffixes are not easily available to an LR
parser generator (without using hacks such as negative offsets into the stack).
However if we consider recursive descent parsing, each function corresponding
to the non-terminals could take the previous type it "wraps" as a parameter,
circumventing this problem.

```
; The algorithm using recursive descent is described using a hyptohetical extension
; of a parser generator where non-terminals can be parameterized by their context.

<declaration>    ::= <prefix> IDENTIFIER                    => ($1, $2)
                   | <prefix> IDENTIFIER <suffix($1)>       => ($3, $2)

<prefix>         ::= int                                    => Type::Integer
                   | void                                   => Type::Void
                   | <prefix> *                             => Type::Pointer($1)

<suffix(prev)>   ::= [ <expr> ] <suffix(prev)>              => Type::Array($4, $2)
                   | ( <declaration-list> ) <suffix(prev)>  => Type::Function($4, $2)
                   | [ <expr> ]                             => Type::Array(prev, $2)
                   | ( <declaration-list> )                 => Type::Array(prev, $2)
```

Now we re-introduce declarator grouping using paranthesis and discuss how this
leads to the chicken-and-egg problem. This requires turning `prefix` into
a parametric parsing function like `suffix`, and re-introducing the non-terminal
`<declarator>` that parenthesis can recurse to.

From reading the obvious implementation below the problem is apparent, the
fourth production for `declarator` calls a parametric parsing function with
a parameter that couldn't possible have been constructed by any left-to-right
parser at the time when the parameter is needed. This is because the
parenthised declarator "wraps" both the prefixes and suffixes of the outer
declarator.


```
<declaration>      ::= <type-specifier> <declarator($1)>                => $2

; The fourth production of this non-terminal has an impossible forward reference
<declarator(prev)> ::= <prefix(prev)> IDENTIFIER                        => ($1, $2)
                     | <prefix(prev)> IDENTIFIER <suffix($1)>           => ($3, $2)
                     | <prefix(prev)> ( <declarator($1)> )              => $3
                     | <prefix(prev)> ( <declarator($5)> ) <suffix($1)> => $3

<prefix(prev)>     ::= *                                                => Type::Pointer(prev)
                     | <prefix> *                                       => Type::Pointer($1)

<suffix(prev)>     ::= [ <expr> ] <suffix(prev)>                        => Type::Array($4, $2)
                     | ( <declaration-list> ) <suffix(prev)>            => Type::Function($4, $2)
                     | [ <expr> ]                                       => Type::Array(prev, $2)
                     | ( <declaration-list> )                           => Type::Array(prev, $2)
```

### 5.1. The time-travellers solution

The first proposed solutions is to deviate from traditional left-to-right
parsing, and make the parser rewindable. This can be done by either pre-lexing
the entire input file into a list of tokens, or if lexing a seekable input,
making the lexical analyzer's state restorable.

```
; The declarative notation above is hardly adequate for describing how this
; solves the problem, thus an explicit imperative notation is used here.

; The function below implements the following production rule:
;  <prefix(prev)> ( <declarator($5)> ) <suffix($1)> => $3

declarator(prev) {
   ; Obtain the value of $1 as normal
   let $1 = <prefix(prev)>
   match (
   ; Save the parser state just before the nested declarator
   let S1 = save_state()
   ; Assume a non-parametric version of declarator also exists.
   ; This would just consume the declarator but produce no results.
   <declarator>
   match )
   ; Now we will be able to obtain the value of $5
   let $5 = <suffix($1)>
   ; Save the state at the end of the declarator
   let S2 = save_state()
   ; Restore the state for the nested declarator and parse it,
   ; now with the value of $5 available.
   restore_state(S1)
   let $3 = <declarator($5)>
   ; Then we can restore to the end and return $3
   restore_state(S2)
   $3
}
```

This does solve the problem and keep our type construction scheme intact,
however it adds a lot of complexity to the parsing machinery, and a second
pass over nested declarators.

Nontheless this scheme is used by some compilers such as rui314's chibicc.
In chibicc's case it is easy to implement as the entire token stream is
available as a linked list, thus `save_state` and `restore_state` are just
one pointer assignment. However this solutions falls short of the "one pass"
claim of the section title.

### 5.2. Backpatching the type

Another solution to the problem is relaxing our construction scheme. In reality
programming languages usually implement recursive types by containing pointers
with the member of the same type being stored in a different allocation.

This way we can resolve the forward dependency by providing a pointer to an
allocation with the required size, but placeholder contents. Then later, when
the correct contents are known we can overwrite the placeholder.
The only downside is that we cannot do semantic checking in the constructor of
types, as obviously the constructor cannot determine if the placeholder
type will be a valid member.

The semantic checking problem can be resolved by either another pass over the
entire type structure (not going to be explored as we've already explored
multiple two pass solutions). Or by declarators returning a reference to the
function that must be used to check the replacement of the placeholder type when
it is available.

```
declarator(prev) {
   let $1 = <prefix(prev)>
   match (
   let placeholder = alloc
   let ($3, checker) = <declarator(placeholder)>
   match )
   let $5 = <suffix($1)>
   checker($5)
   write placeholder, $5
   $3
}
```

This solution is implemented by rui314's 8cc minus the delayed semantic
checking, that compiler just makes the assumption that the source program
doesn't contain nonsensical types like a function returning an array.
This is acceptable the compiler is only required to exhibit deterministic
behavior on compliant programs, however it is highly inconvenient to the user.

With that said this solution with delayed semantic checking seems workable,
and there are probably production compilers that use it. However the result
will probably look like the kind of code that will make the unsuspecting CS
student want to quit programming forever. It also interferes with certain memory
management scheme like interning or reference counting.

## 6. Who said one pointer is enough?

Could the "true rockstar", not afraid of one, two, or even three layers of
indirection solve this problem with less hacks?
Perhaps, we can learn from the "real programmers" of the last century and even
take the address of a couple pointers ourselves.

Going back to the clean grammar from Section 4, and thinking "inside-out" we
can observe that it is possible to provide the address of the location that will
have to contain the pointer to the type to be constructed to the action code.
Downside is we will need to construct types before their members, but combining
this with the delayed type checking idea from Section 5, we end up with a
working solution with the obvious grammar.

```
; I won't even attempt to describe this algorithm in any notation other than C
; The delayed type checking makes this even uglier and implementing it left as
; an "exercise" to the reader :)

declarator(Type **out_head, Type ***out_tail, String *out_name)
{
    if (maybe_want(TK_MUL)) {
        declarator(out_head, out_tail);
        **out_tail = Type::Pointer;
        *out_tail = &(***out_tail).base_type;
    } else {

    if (maybe_want(TK_LPAREN)) {
        declarator(out_head, out_tail, out_name);
        want(TK_RPAREN);
    } else {
        want(TK_IDENTIFIER);
    }

    for (;;)
        if (maybe_want(TK_LSQ)) {
            let cnt = expr();
            want(self, TK_RSQ);
            **out_tail = Type::Array(cnt);
            *out_tail = &(***out_tail).elem_type;
        } else if (maybe_want(TK_LPAREN)) {
            let param_types = declaration_list();
            want(self, TK_RPAREN);
            **out_tail = Type::Function(param_types);
            *out_tail = &(***out_tail).elem_type;
        } else {
            break;
        }
    }
}

declaration()
{
    // Here is how to call this
    let head = NULL;
    let tail = &head;
    let name;
    declarator(&head, &tail, &name);
    *tail = base_type;

    // Then finally (head, name) is the value of the declaration
    (head, name)
}
```

This took many tries to get (hopefully) correct, and is very hard to understand,
or reason about. However it is a legitimate way of parsing C declarators in one
pass, thus it is included here for completeness.
