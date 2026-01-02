```
ASTNode (абстрактный базовый)

ModuleNode
- decls: List[DeclarationNode]

DeclarationNode (абстрактный)
- DefineDecl
  - id: Identifier
  - value: ExprNode
- VarDecl
  - id: Identifier
  - type: TypeExpr
  - init: ExprNode
- FieldDecl
  - name: Identifier
  - type: TypeExpr
- FunctionDecl
  - signature: FnSignature        // функция как значение — НЕ имеет имени; FunctionDecl это нода только если нужно именованное значение via DefineDecl
  - body: List[Statement]         // тело всегда присутствует (всегда >=0 stmt)
- PubDecl
  - inner: DeclarationNode        // pub wraps exactly one DeclarationNode

ExprNode (абстрактный)
- Name
  - parts: List[Identifier]       // length >= 1
- FuncCall
  - func: ExprNode                // can be Name or any ExprNode
  - args: List[ExprNode]          // possibly empty
- LiteralString
  - value: str
- LiteralInt
  - value: int
- LiteralReal
  - value: float
- ListLiteral
  - items: List[ExprNode]
- StructLiteral
  - items: List[ExprNode]
- AddressOf
  - name: Name                    // '&' applied to a Name
- UndefinedLiteral               // singleton node
- UnaryOp
  - op: str
  - expr: ExprNode
- BinaryOp
  - left: ExprNode
  - op: str
  - right: ExprNode
- FnExpr                        // anonymous function expression
  - params: List[Field]
  - ret: TypeExpr
  - body: List[Statement]        // body always present

TypeExpr (абстрактный)
- PureType
  - name: Name
- PointerType
  - inner: TypeExpr
- ArrayType
  - length: ExprNode
  - inner: TypeExpr
- SliceType
  - inner: TypeExpr
- FnType
  - signature: FnSignature
- StructType
  - module: ModuleNode

FnSignature
- params: List[Field]            // possibly empty
- ret: TypeExpr                  // return type (use PureType("void") when void)

Field
- name: Identifier
- type: TypeExpr

Statement (абстрактный)
- LocalSymbolDecl
  - symbol: DefineDecl
- LocalVarDecl
  - variable: VarDecl
- Assign
  - target: Name
  - value: ExprNode
- CallStmt
  - call: FuncCall
- ReturnStmt
  - expr: ExprNode                // if omitted in source, represent with UndefinedLiteral
- ExprStmt
  - expr: ExprNode

Identifier (leaf)
- name: str

```