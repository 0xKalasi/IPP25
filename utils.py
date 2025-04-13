# Project: IPP 1. part ( SOL25 code analyzer )
# Author: Tomáš Bordák (xborda01)
# Date: 18-03-2025
# File: utils.py

import sys
from lark import Visitor, Token
from error_codes import *

########################## KEYWORDS AND SYNTAX CHECKS ########################## 
KEYWORDS = { "class", "self", "super", "nil", "true", "false" }

class checkKeywords( Visitor ):
    def block_stat( self, tree):
        return self.checkIDKeyword( tree )
    
    def selector( self, tree ):
        return self.checkIDKeyword( tree )
    
    def expr_tail( self, tree ):
        return self.checkIDKeyword( tree )
    
    def block_par( self, tree ):
        return self.checkIDKeywordStartColon( tree )
    
    def checkIDKeyword( self, tree ):
        if tree.children:
            id = tree.children[0]
            if id in KEYWORDS:
                print(f"Syntax error in input code", file=sys.stderr)
                sys.exit(SYN_ERROR)
        return self
    
    def checkIDKeywordStartColon( self, tree ):
        if tree.children:
            id = tree.children[0] # token ID
            if id in {":" + kw for kw in KEYWORDS}: # check for ":[KEYWORDS]" 
                print(f"Syntax error in input code", file=sys.stderr)
                sys.exit(SYN_ERROR)
        return self


########################## SEMANTIC CHECKS ########################## 
class semanticChecks( Visitor ):
    def __init__( self, defClasses):
        self.definedClasses = defClasses
        self.definedVariables = []

    def class_rule( self, tree ):
        # second CID in class_rule is superclass (class, from which the first CID inherits)
        nameSuper = tree.children[1].value
        self.checkClassDefined( nameSuper )
        return tree

    def expr( self, tree):
        expr_base = tree.children[0].children[0]

        # if expr_base is expr rule -> '(' expr ')' -> just return and run expr again
        if not isinstance( expr_base, Token):
            return self
        
        nodeType = tree.children[0].children[0].type
        nodeVal = tree.children[0].children[0].value

        # check CID and method 
        if nodeType == "CID":
            self.checkClassDefined( nodeVal )
            methods = self.definedClasses[nodeVal]

            # move to expr_tail to check method
            expr_tail = tree.children[1].children[0]
            if isinstance( expr_tail, Token ): # we got ID -> method
                method = tree.children[1].children[0].value
                if not method in methods:
                    print( f"Semantic error: method '{ method }' is not defined on class { nodeVal }", file=sys.stderr )
                    sys.exit( SEM_UNDEFINED_ERROR )

        # check expr_sel rule
        expr_sel = tree.children[1].children[0].children # expr_sel tree

        if len(expr_sel) != 0 and nodeType == 'CID':
            # expr_sel is not eps
            cls = nodeVal
            method = expr_sel[0].value # ID_COLON_END = method name
            methods = self.definedClasses[cls]["methods"] # methods of the CID in expr_sel -> expr_base

            if not method in methods:
                print( f"Semantic error: method '{ method }' is not defined on class { nodeVal }", file=sys.stderr )
                sys.exit( SEM_UNDEFINED_ERROR )
            
            # starting point when more than 1 expr_sel rule occured in this tree
            secExprSel = expr_sel[2].children

            # check all ID_COLON_END from expr_sel rules in the expr_sel tree -> expr_sel variable
            while len(secExprSel) != 0:
                method = secExprSel[0].value # ID_COLON_END
                
                if not method in methods:
                    print( f"Semantic error: method '{ method }' is not defined on class { nodeVal }", file=sys.stderr )
                    sys.exit( SEM_UNDEFINED_ERROR )

                secExprSel = secExprSel[2].children

        return tree
    
    def block( self, tree ):
        block_par = tree.children[0]    # block params tree
        block_stat = tree.children[1]   # block body tree
        params = []                     # params list to check against vars (collision)
        vars = []                       # vars list (collision)

        # 1) fill vars list to check if there is not collision with params
        # 2) find undefined IDs in expr_base rule
        while block_stat.children and isinstance(block_stat.children[0], Token):
            vars.append(block_stat.children[0].value) # fill vars 
            
            # check if expr_base isnt containing ID that is undefined
            for expr_base in block_stat.find_data("expr_base"):
                tok = expr_base.children[0]

                # check if there is not '(' expr ')' rule, we want Token here
                if isinstance( tok, Token ) and tok.type == 'ID':
                    if tok.value not in params and tok.value not in vars:
                        print( f"Semantic error: variable { tok } is not defined", file=sys.stderr )
                        sys.exit( SEM_UNDEFINED_ERROR )

            block_stat = block_stat.children[2] # move to next ID

        # first param -> block_par[0]
        # second param -> block_par[1].children[0] 
        # third param -> block_par[2].childen[0]
        if len(block_par.children) != 0:
            # params
            while block_par.children and isinstance(block_par.children[0], Token):
                par = block_par.children[0].value[1:] # [1:] -> save from index 1 to end (slice starting ':' from param name)
                if not par in params:
                    params.append(par)  
                else: 
                    print( f"Semantic error: block parameter '{ par }' was already defined as block parameter.", file=sys.stderr )
                    sys.exit( SEM_OTHER_ERROR    )
                block_par = block_par.children[1]     # go to subtree -> another block_par rule

            # check for collision between block params and block body IDs
            for id in vars:
                if id in params:
                    print( f"Semantic error: variable '{ id }' is already a block parameter.", file=sys.stderr )
                    sys.exit( SEM_COLISSION_ERROR )            

        return self
          
    def checkClassDefined( self, CID ):
        if CID not in self.definedClasses:
            print( f"Semantic error: class { CID } is not defined", file=sys.stderr )
            sys.exit( SEM_UNDEFINED_ERROR )
        return self
    
class definedClasses( Visitor ):
    def __init__( self ):
        # define builtIn classes (with its methods) to allClasses right at the start
        self.allClasses = { 
            "Object": {
                "inherits": "",
                "inheritDone": True,
                "methods": { 'new', 'from:' , 'identicalTo:', 'equalTo:', 'asString', 'isNumber', 'isString', 'isBlock', 'isNil' }, 
            }, 
            "Nil": {
                "inherits": "Object",
                "inheritDone": False,
                "methods": {}
            }, 
            "True": {
                "inherits": "Object",
                "inheritDone": False,
                "methods": { 'not', 'and:', 'or:', 'ifTrue:ifFalse:' }
            }, 
            "False":{
                "inherits": "Object",
                "inheritDone": False,
                "methods": { 'not', 'and:', 'or:', 'ifTrue:ifFalse:' }
            }, 
            "Integer": {
                "inherits": "Object",
                "inheritDone": False,
                "methods": { 'greaterThan:', 'plus:', 'minus:', 'multiplyBy:', 'divBy', 'asInteger', 'timesRepeat:' }
            }, 
            "String": {
                "inherits": "Object",
                "inheritDone": False,
                "methods": { 'read', 'print', 'asInteger', 'concatenateWith:', 'startsWith:endsBefore:' }
            }, 
            "Block": {
                "inherits": "Object",
                "inheritDone": False,
                "methods": { 'whileTrue:' }
            } 
        }
 
        # currentClass for assigning methods to the right class
        self.currentClass = None
    
    # save classes present in tree
    def class_rule( self, tree ):
        # first CID in class_rule is new class name
        name = str( tree.children[0].value )
        
        if name in self.allClasses:
            print( f"Semantic error: redefinition of class { name }.", file=sys.stderr )
            sys.exit( SEM_OTHER_ERROR )
        
        self.currentClass = name

        # second CID in class_rule is the superclass
        superclass = tree.children[1].value

        self.allClasses[ name ] = {
            "inherits": superclass,
            "inheritDone": False,
            "methods": set()
        }
        return self
       
    # save all methods that are defined in each class
    def method( self, tree ):
        if tree.children:
            name = tree.children[0].children[0].value
            methodsSet = self.allClasses[self.currentClass]["methods"]

            # check if method run in Main class has any params (should have none)
            if self.currentClass == "Main" and name == "run":
                block_parTree = tree.children[1].children[0].children
                if block_parTree: 
                    # block_par is eps
                    print( "Semantic error: class Main - non-parametric method 'run' has parameters.", file=sys.stderr )
                    sys.exit( SEM_ARITY_ERROR )
            
            # check if method isnt already in methods (redefition)
            if name in methodsSet:
                print( f"Semantic error: redefinition of method '{ name }' on class { self.currentClass }.", file=sys.stderr )
                sys.exit( SEM_OTHER_ERROR )
            else:
                methodsSet.add( name )
        return self
    
    def checkMain( self ):
        classes = self.allClasses

        if "Main" not in classes:
            print( "Semantic error: class Main is not defined", file=sys.stderr )
            sys.exit( SEM_MAIN_RUN_ERROR )

        if not 'run' in classes[ 'Main' ][ 'methods' ]:
            print( "Semantic error: method 'run' is not defined in class Main", file=sys.stderr )
            sys.exit( SEM_MAIN_RUN_ERROR )
        
        return self
    
    def inherit( self ):
        # check for circular inheritance
        if foundCircle( self.allClasses ):
            print( f"Semantic error: classes circular inheritance", file=sys.stderr )
            sys.exit( SEM_OTHER_ERROR )
        
        notInheritedYet = list()
        
        # fill the list with all defined classes
        for cls in self.allClasses:
            notInheritedYet.append( cls )
        
        # go to "inherits" of each class, get that class name and its methods (from where should the class inherit)
        # and add these to "methods" of each class
        while len(notInheritedYet) != 0:
            for cls in notInheritedYet:
                # superclass that the 'cls' wants to inherit from
                inheritsFrom = self.allClasses[cls]["inherits"]
                inheritDone = self.allClasses[cls]["inheritDone"]

                if not inheritDone:
                    # check if the superclass is defined
                    if not inheritsFrom in self.allClasses:
                        print( f"Semantic error: class { inheritsFrom } is not defined", file=sys.stderr )
                        sys.exit( SEM_UNDEFINED_ERROR)

                    superclassIsDone = self.allClasses[inheritsFrom]["inheritDone"]

                    # if superclass inherited from its superclass
                    if superclassIsDone:
                        inheritedMethods = self.allClasses[inheritsFrom]["methods"] # methods of superclass
                        clsMethods = self.allClasses[cls]["methods"] # methods of 'cls'

                        if len(clsMethods) == 0:
                            self.allClasses[cls]["methods"] = inheritedMethods
                        else:
                            self.allClasses[cls]["methods"].update( inheritedMethods )
                        
                        # set class to inherited, so other classes waiting on that can inherit too
                        self.allClasses[cls]["inheritDone"] = True
                else:
                    # 'cls' inherited already
                    notInheritedYet.remove( cls )
            
        return self
    
def foundCircle( allClasses ):
    # recursive search of inheritance circle
    # stack is for keeping the actual track 
    # recursively go down in defined classes, then go back and look if the ends dont connect
    def search( cls, visited, stack ):
        # go out of recursion
        if cls in stack: 
            return True

        # visited already, dont need to go to that class again
        if cls in visited: 
            return False

        visited.add( cls )
        stack.add( cls )

        superclass = allClasses[cls]["inherits"]
        if superclass in allClasses:
            if search(superclass, visited, stack):  
                return True  # return true also -> go back from recursing deeper

        # remove the class from stack, since its not in circle
        stack.remove(cls)  
        return False

    visited = set()

    # run search for all classes
    for cls in allClasses:
        if cls not in visited:
            if search(cls, visited, set() ):
                return True  # found circle

    return False # didnt find circle
    

########################## OTHERS ########################## 
def printUsage():
    print("Usage:\n")
    print("Reads SOL25 source code from standard input, checks lexical, syntactic and static semantic correctness of the code and prints XML representation of AST of the SOL25 program to the standard output.")
    print("\nExample:     python3.11 parse.py < FILE")
    print("Options:")
    print("     --help      Show this usage and exit")
    sys.exit(0)