# Project: IPP 1. part ( SOL25 code analyzer )
# Author: Tomáš Bordák (xborda01)
# Date: 18-03-2025
# File: parse.py

import sys
from lark import Lark, UnexpectedCharacters, UnexpectedToken

from error_codes import *
from utils import printUsage, definedClasses, checkKeywords, semanticChecks

grammar = r"""

    program: (class_rule program)*                      // Program -> Class Program
                                                        // Program -> eps
                                                    
    class_rule: "class" CID ":" CID "{" method "}"      // Class -> class <CID> : <CID> { Method }
    
    method: (selector block method)*                    // Method -> Selector Block Method
                                                        // Method -> eps
    
    selector: ID | ID_COLON_END selector_tail           // Selector -> <id>
                                                        // Selector -> <id:> SelectorTail

    selector_tail: (ID_COLON_END selector_tail)*        // SelectorTail -> <id:> SelectorTail
                                                        // SelectorTail -> eps
    
    block: "[" block_par "|" block_stat "]"             // Block -> [ BlockPar | BlockStat ]

    block_par: (ID_COLON_START block_par)*              // BlockPar -> <:id> BlockPar
                                                        // BlockPar -> eps
    
    block_stat: (ID ":=" expr "." block_stat)*          // BlockStat -> <id> := Expr . BlockStat
                                                        // BlockStat -> eps

    expr: expr_base expr_tail                           // Expr -> ExprBase ExprTail
    
    expr_tail: ID | expr_sel                            // ExprTail -> <id>
                                                        // ExprTail -> ExprSel
    
    expr_sel: (ID_COLON_END expr_base expr_sel)*        // ExprSel -> <id:> ExprBase ExprSel
                                                        // ExprSel -> eps

    expr_base: INT | STR | ID | CID | block | "(" expr ")"      // ExprBase -> <int> | <str> | <id> | <Cid>
                                                                // ExprBase -> Block        
                                                                // ExprBase -> ( Expr )
                                      
    ID: /[a-z_][A-za-z0-9_]*/
    CID: /[A-Z][A-Za-z0-9]*/
    ID_COLON_END: /[a-z_][A-za-z0-9_]*:/
    ID_COLON_START: /:[a-z_][A-za-z0-9_]*/

    INT: /[+-]?[0-9]+/

    STR: /'([^'\\\x00-\x1F]|\\['n\\])*'/                        // STR can contain ASCII above 39(dec) except ' and \
                                                                // there can be escape sequences \' , \n, \\  

    COMMENT: /"([^"\\]|\\")*"/
    %ignore COMMENT
    
    %import common.WS
    %ignore WS

"""
        
parser = Lark(grammar, start="program", parser="lalr")

if len(sys.argv) == 1:
    input = sys.stdin.read()
    try: 
        tree = parser.parse( input )

        # syntax 
        checkKeywords().visit( tree )

        # parse all defined classes and their methods
        classes = definedClasses()
        classes.visit_topdown( tree ) # get the class names from AST

        # check for Main (with run method)
        classes.checkMain() 

        # go trough all defined clases and inherit methods
        classes.inherit()

        # after we got all classes defined in code
        # and check for semantic errors
        semanticChecks( classes.allClasses ).visit( tree )

    # catch errors from .parse (lex and some syntax errors when run trough grammar)
    except UnexpectedCharacters as e: 
        print( f"Lexical error: {e}", file=sys.stderr )
        sys.exit( LEX_ERROR ) 
    except UnexpectedToken as e:
        print( f"Syntax error: {e}", file=sys.stderr )
        sys.exit( SYN_ERROR ) 
    
elif len( sys.argv ) == 2 and sys.argv[1] == "--help":
    printUsage()

elif len( sys.argv ) > 1:
    print( "Error: Invalid arguments. Use --help for usage.", file=sys.stderr )
    sys.exit(10)