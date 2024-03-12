"""
parse_rules.py

Rules follow the language

S -> (S)
S -> S | S
S -> MONTH
S -> DAY
S -> YEAR
S -> HOUR
S -> MINUTE
MINUTE -> RANGE(MINUTE, MINUTE)
DAY -> RANGE(DAY, DAY)
YEAR -> RANGE(YEAR, YEAR)
MONTH -> RANGE(MONTH, MONTH)

RANGE is just union of several items of the same raw type

MONTH,DAY,YEAR,MIN,HOUR nodes all have same type
theu can get converted to nodes of type RorN
Range nodes are of type RorN
Unions can only happen between nodes of type RorN
RorN nodes can get converted to same type as union

parens can only close nodes of type union

RULES:
below       |   pop     |   read    |   next    |   push    |
# turning input into nodes
$,NODE,(,|  |   &       |   Mint    |           |MONTH(int) |
$,NODE,(,|  |   &       |   dint    |           | DAY(int)  |
$,NODE,(,|  |   &       |   yint    |           | YEAR(int) |
$,NODE,(,|  |   &       |   mint    |           | MIN(int)  |
$,NODE,(,|  |   &       |   hint    |           | HOUR(int) |
# turning ranges into range nodes
INT         |   &       |   -       |           |   -
$,(,NODE    |MONTH-MONTH|   &       |           | RANGE(a,b)| # this rule is repeated for every node type

# unions RorN => type is range or finished int node
$ (         |FINAL FINAL|    &      |           | UNION(a,b)|

# paren rules
            | (finished)|   &       |           | RorN(a)
any         |   &       |   (       |           | (
union       |   &       |   )       |           | ) # might want to combine this with the first paren rule


"""
#from cp1.nfa import NFA
import sys

# rules structured as below, pop, read, next, push
# below and next are sets, pop, read, and push are strings
# empty next sets mean anything can be next
# TODO: find better way to represent functions
# TODO: sub symbol for '⊣' <- that is the terminal symbol (end of string)
# TODO: figure out what this means: U \ {*}
class Node:
    def __init__(self, operation: str = "", cfg_type: str = "NONE", parameters = []):
        # if these matches dont work, will need to add the CFG symbol that goes with the state
        assert type(operation) is str, f"invalid construction, operation is not a string: {operation}"
        self.operation = operation
        assert type(parameters) is list, f"invalid construction, parameters are not a list: {parameters}"
        self.parameters = parameters
        assert type(cfg_type) is str, f"invalid construction, cfg_type is not a string"
        self.cfg_type = cfg_type

    def __repr__(self):
        return f"{self.operation}{self.cfg_type}({",".join(str(p) for p in self.parameters)})"
    
    def __eq__(self, other):
        if type(other) == type(self):
            return other.cfg_type == self.cfg_type
        return False
    
    def __ne__(self, other):
        if type(other) == type(self):
            return other.cfg_type != self.cfg_type
        return True
    
    def __hash__(self):
        return hash(str(type(self))+self.cfg_type)

# TODO: see if I can cut out some rules
# if the popped item is a str, just treat it as normal
# if the popped item is a Node, just make sure the popped type is also a Node
# in these rules, 'a' is any char that isnt a reserved symbol
RESERVED_SYMBOLS = {'(', ')', '|', '*'}
# TODO redo RULES to incorporate typing used by chiang
RULES = [
    # rules for reading input
    [{'$', '(', '|', Node()}, ['&'], 'a', set(), Node('symbol')], # a, & -> a for a in E
    [{'$', '(', '|', Node()}, ['&'], '(', set(), '('], # (, & -> (
    [{Node()}, ['&'], ')', set(), ')'], # ), & -> )
    [{Node()}, ['&'], '|', set(), '|'], # |, & -> |
    [{Node()}, ['&'], '*', set(), '*'], # *, & -> *
    # rules for converting input to nodes
    #[{}, ['Ea', '|', 'Mb'], '&', {}, 'Eunion(a, b)'], # ε, E|M → E
    [set(), [Node(), '|', Node()], '&', set(), Node('union')], # ε, E|M → E

    # I think this is unnecessary
    #[{'$', '('}, ['Ma'], '&', {}, 'Ea'], # ε, M → E

    #[{'$', '(', '|'}, ['&'], '&', {'|', '(', '⊣'}, 'Mepsilon()'], # ε, ε → M
    [{'$', '(', '|'}, ['&'], '&', {'|', ')', '⊣'}, Node('epsilon')], # ε, ε → M

    # I think this one is also unnecessary
    #[{}, ['Ta'], '&', {'|', ')', '⊣'}, 'Ma'], # ε,T → M

    #[{}, ['Ta', 'Fb'], '&', {}, 'Tconcat(a, b)'], # ε,TF → T
    [set(), [Node(), Node()], '&', set(), Node('concat')], # ε,TF → T

    # this one also might not be needed
    #[{'$', '(', '|'}, ['Fa'], '&', {}, 'Ta'], # ε, F → T

    #[{}, ['Pa', '*'], '&', {}, 'Fstar(a)'], # ε, P* → F
    [set(), [Node(), '*'], '&', set(), Node('star')], # ε, P* → F

    # I think this is supposed to be the terminal character, but will have to check
    # might not be necessary
    #[{}, ['Pa'], '&', {'U \ {*}'}, 'Fa'], # ε, P → F

    #[{}, ['a'], '&', {}, 'Psymbol(a)'], # ε, a → P for a ∈ Σ
    [set(), ['a'], '&', set(), Node('symbol')], # ε, a → P for a ∈ Σ

    # this just removes parenthesese that only have one item in them
    #[{}, ['(', 'Ea', ')'], '&', {}, 'Pa'], # ε, (E) → P
    [set(), ['(', Node(), ')'], '&', set(), Node('input')], # ε, (E) → P

]

def parser(regex: str):
    """
    basic approach:
        List of transitions are all possible transitions.
        For every char, find the transition that matches the input/stack 
    
    TODO: fix union
    TODO: fix star
    
    """
    # TODO: add 'end of string character'
    remaining_input = list(regex)
    stack = ['$']
    # when the stack does not change, it means we have an invalid regex (because we should always follow exactly one rule)
    a_rule_was_followed = True

    while a_rule_was_followed:
        print(f"remaining input: {remaining_input}")
        print(f"stack: {stack}")
        next_input = remaining_input.pop(0) if len(remaining_input) > 0 else "&"
        a_rule_was_followed = False
        for rule in RULES:
            # basic idea is to make sure the rule is valid, and if it is - to do do it
            # if it isnt valid, just skip that rule
            invalid = False
            below, pop, read, next_token, push = rule
            # make sure the rules are well formed
            assert type(below) is set, f"failed to read below from rule {rule}"
            assert type(pop) is list, f"failed to read pop from rule {rule}"
            assert type(read) is str, f"failed to read 'read' from rule {rule}"
            assert type(next_token) is set, f"failed to read next_token from rule {rule}. Recieved token: {next_token}"
            assert type(push) is str or Node, f"failed to read push from rule {rule}. Recieved token: {push}"
            print(f"checking rule: {rule}")
            # if the top of the stack is not in 'below' and 'below' exists then the rule is invalid
            if stack[-1] not in below and below:
                print(f"top of stack is not in below.\ntop of stack: {stack[-1]} not in {below}")
                invalid = True
            # if we pop nothing then its fine
            if pop != ['&']:
                # make sure the stack has what is about to be popped
                for index, item in enumerate(pop):
                    if stack[-1 - (len(pop) - index - 1)] != item:
                        print(f"item {item} was not next in the stack - comparison: {stack[-1 - (len(pop) - index -1)]}")
                        invalid = True
                        break
                
            if next_input != read and read != '&' and read != 'a':
                print(f"wrong read: {next_input} != {read}")
                invalid = True

            if read == 'a':
                if next_input in RESERVED_SYMBOLS or next_input == '&':
                    print(f"wrong read value - {read} != {next_input}")
                    invalid = True
            if len(remaining_input) > 0 and len(next_token) > 0:
                if next_token and remaining_input[0] not in next_token:
                    print(f"invalid next token: {remaining_input[0]} not in {next_token}")
                    invalid = True

            if invalid:
                continue
            # now all of the conditions should be met, so we can perform the operation
            # pop the old items
            print(f"following rule: {rule}")
            popped_from_stack = []
            for item in pop:
                if item == "&":
                    continue
                popped_item = stack.pop()
                if popped_item not in RESERVED_SYMBOLS:
                    popped_from_stack.append(popped_item)
                else:
                    # ignored reserved symbol
                    pass
                
            pushed_item = push
            # todo: make this work for functions
            if push == Node():
                # If we are making a symbol node, the parameter should be the token we read in, since nothing should have been popped from the stack
                if push.operation == 'symbol':
                    assert len(popped_from_stack) == 0, f"bad parsing, was supposed to push a symbol, but popped values from the stack: {popped_from_stack}"
                    popped_from_stack = [next_input]
                pushed_item = Node(push.operation, parameters=popped_from_stack)
            stack.append(pushed_item)



            a_rule_was_followed = True
            break
        # if we are at the end of the input and there is only one token left in the stack (it has to be a Node) then return that node
        if len(remaining_input) == 0 and len(stack) == 2:
            assert type(stack[-1]) is Node, f"whoops, the last thing on the stack was not a Node, instead it was: {stack}"
            return stack.pop()
        assert a_rule_was_followed, "this is unnecessary, but whatever, the loop will break anyways if a rule isnt performed"

def main():
    """
    Main driver for program
    """
    args = sys.argv[1:]
    if len(args) != 1:
        raise RuntimeError(f"Incorrect number of arguments.\nExpected 1, got {len(args)}")
    print(parser(args[0]))


if __name__ == "__main__":
    main()