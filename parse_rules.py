"""
parse_re.py

CP 2 Part 1
Parse a regular expression and return a syntax tree
"""
import sys

# rules structured as below, pop, read, next, push
# below and next are sets, pop, read, and push are strings
# empty next sets mean anything can be next
class Node:
    def __init__(self, operation: str = "NONE", cfg_type: str = "NONE", parameters = []):
        # if these matches dont work, will need to add the CFG symbol that goes with the state
        assert type(operation) is str, f"invalid construction, operation is not a string: {operation}"
        self.operation = operation
        assert type(parameters) is list, f"invalid construction, parameters are not a list: {parameters}"
        self.parameters = parameters
        assert type(cfg_type) is str, f"invalid construction, cfg_type is not a string"
        self.cfg_type = cfg_type
    
    def __str__(self):
        params = []
        for p in self.parameters:
            if type(p) is Node:
                params.append(str(p))
            else:
                if p != "&":
                    params.append('"' + str(p) + '"')
        return f"{self.operation}({','.join(params)})"
    

    def __repr__(self):
        return f"{self.operation}{self.cfg_type}({','.join(str(p) for p in self.parameters)})"
    
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

# if the popped item is a str, just treat it as normal
# if the popped item is a Node, just make sure the popped type is also a Node
# in these rules, 'a' is any char that isnt a reserved symbol
RESERVED_SYMBOLS = {'(', ')', '|', '*', '⊣', '$'}
RULES = [
    # rules for reading input
    [{'$', '(', '|', Node(cfg_type='T')}, ['&'], 'a', set(), 'a'], # a, & -> a for a in E
    [{'$', '(', '|', Node(cfg_type='T')}, ['&'], '(', set(), '('], # (, & -> (
    [{Node(cfg_type='E')}, ['&'], ')', set(), ')'], # ), & -> )
    [{Node(cfg_type='E')}, ['&'], '|', set(), '|'], # |, & -> |
#    [{Node(cfg_type='P')}, ['&'], '*', set(), '*'], # *, & -> *
    # rules for converting input to nodes
    [set(), [Node(cfg_type='E'), '|', Node(cfg_type='M')], '&', set(), Node('union', cfg_type='E')], # ε, E|M → E
    [{'$', '('}, [Node(cfg_type='M')], '&', set(), Node(cfg_type='E')], # ε, M → E
    [{'$', '(', '|'}, ['&'], '&', {'|', ')', '⊣'}, Node('epsilon', cfg_type='M')], # ε, ε → M
    [set(), [Node(cfg_type='T')], '&', {'|', ')', '⊣'}, Node(cfg_type='M')], # ε,T → M
    [set(), [Node(cfg_type='T'), Node(cfg_type='F')], '&', set(), Node('concat', cfg_type='T')], # ε,TF → T
    [{'$', '(', '|'}, [Node(cfg_type='F')], '&', set(), Node(cfg_type='T')], # ε, F → T
#    [set(), [Node(cfg_type='P'), '*'], '&', set(), Node('star', cfg_type='F')], # ε, P* → F
    # next character cannot be a star
    [set(), [Node(cfg_type='P')], '&', {'NOT_STAR'}, Node(cfg_type='F')], # ε, P → F
    [set(), ['a'], '&', set(), Node('symbol', cfg_type='P')], # ε, a → P for a ∈ Σ
    # this just removes parenthesese that only have one item in them
    [set(), ['(', Node(cfg_type='E'), ')'], '&', set(), Node(cfg_type='P')], # ε, (E) → P
]

def check_rule(rule, stack, input_str) -> bool:
    """
    Separate function to check rules so the main parser loop is less cluttered
    Returns a boolean if the rule is allowed

    the token below whatever is getting popped must be in the set {below}
    every item in [pop] must be at the top of the stack in the reverse order they are presented (last first)
    the value read from the input string must be equal to *read*. the character 'a' means any character that is not a RESERVED_SYMBOL
    and '&' means nothing was read from the input string
    the value after read in the input string must be found in the set {next_token}
    """
    below, pop_tokens, read, next_tokens, push_token = rule
    # make sure the rules are well formed
    assert type(below) is set, f"failed to read below from rule {rule}"
    assert type(pop_tokens) is list, f"failed to read pop from rule {rule}"
    assert type(read) is str, f"failed to read 'read' from rule {rule}"
    assert type(next_tokens) is set, f"failed to read next_token from rule {rule}. Recieved token: {next_tokens}"
    assert type(push_token) is str or Node, f"failed to read push from rule {rule}. Recieved token: {push_token}"
    
    # check below tokens
    below_index = (len(pop_tokens) + 1)  * -1 if pop_tokens != ['&'] else -1
    if below:
        if len(stack) <= (below_index * -1) -1:
            return False
        if stack[below_index] not in below:
            return False
        
    
    # check pop items
    if pop_tokens != ['&']:
        stack_pop_items = stack[below_index + 1:]
        if pop_tokens == ['a']:
            if len(stack_pop_items) != 1:
                return False
            if stack_pop_items[0] in RESERVED_SYMBOLS:
                return False
            if type(stack_pop_items[0]) is Node:
                return False
        elif stack_pop_items != pop_tokens:
            return False
    
    # check read value
    # all node rules do not read from the input string
    # if we arent supposed to read anything then dont worry too much about it
    if read != '&':
        # if we are supposed to read something but there is nothing there, obviously the check fails
        if len(input_str) == 0:
            return False
        if read == 'a':
            # any char that isnt reserved
            if input_str[0] in RESERVED_SYMBOLS:
                return False
            # or a node
            if type(input_str[0]) is Node:
                return False
        # if its a reserved symbol, make sure we are reading in the right one
        elif input_str[0] != read:
                return False
    
    # make sure the next thing in the input is in next_tokens
    if len(next_tokens) != 0:
        next_index = 0 if read == '&' else 1
        if len(input_str) > next_index:
            if 'NOT_STAR' in next_tokens:
                # special case
                if input_str[next_index] == '*':
                    return False
            elif input_str[next_index] not in next_tokens:
                return False
        else:
            if 'NOT_STAR' not in next_tokens:
                return False
    # none of the checks failed so the rule applies
    return True

def parser(regex: str):
    """
    basic approach:
        List of transitions are all possible transitions.
        For every char, find the transition that matches the input/stack 
   
    """
    remaining_input = ['⊣']
    if len(regex) > 0:
        remaining_input = list(regex + '⊣') if regex[-1] != '⊣' else list(regex)
    stack = ['$']
    # when the stack does not change, it means we have an invalid regex (because we should always follow exactly one rule)
    a_rule_was_followed = True

    while a_rule_was_followed:
        #print(f"stack: {stack}")
        a_rule_was_followed = False
        for rule in RULES:    
            """
            Checking rules:
                the token below whatever is getting popped must be in the set {below}
                every item in [pop] must be at the top of the stack in the reverse order they are presented (last first)
                the value read from the input string must be equal to *read*. the character 'a' means any character that is not a RESERVED_SYMBOL
                and '&' means nothing was read from the input string
                the value after read in the input string must be found in the set {next_token}

                if all of those rules are met, 
                every item in pop is popped from the stack
                the value 'read' is read from input
                the value 'push' is pushed to the top of the stack
                    if 'push' is a node:
                        the new node gets the cfg_type of the 'push' node
                        if it does not have an 'operation' then give it the operation of the node that got popped
                            also give it the parameters of the node that got popped
                        if it does have an operation, its parameters are the items that got popped from the stack
                    if 'push' is not a node:
                        push the 'read' value that was obtained from the input
                
                if no rule was met, we are done.
            """
            if not check_rule(rule, stack, remaining_input):
                continue
            
            _, pop_tokens, read, _, push_token = rule
            # now all of the conditions should be met, so we can perform the operation
            # pop the old items

            popped_from_stack = []
            if pop_tokens != ['&']:
                for token in reversed(pop_tokens):
                    popped_token = stack.pop()
                    if pop_tokens != ['a']:
                        assert token == popped_token, f"when popping from stack tokens did not match: {token} != {popped_token}"
                    else:
                        assert token not in RESERVED_SYMBOLS, f"was supposed to pop arbitrary character but instead popped {token}"
                        assert type(token) != Node, f"was supposed to pop arbitrary character but instead popped {token}"
                    if popped_token not in RESERVED_SYMBOLS:
                        popped_from_stack.insert(0, popped_token)
                assert pop_tokens == ['a'] or popped_from_stack == list(filter(lambda x: x not in RESERVED_SYMBOLS, pop_tokens)), f"popped tokens do not match: {popped_from_stack} != {list(filter(lambda x: x not in RESERVED_SYMBOLS, pop_tokens))}"
            
            popped_from_input = ""
            if read != '&':
                assert len(remaining_input) > 0, "tried to pop input from empty list"
                popped_from_input = remaining_input.pop(0)
            
            if type(push_token) is Node:
                assert push_token.cfg_type != 'NONE', f"malformed node: {push_token}"
                new_node = Node(cfg_type=push_token.cfg_type)
                if push_token.operation == 'NONE':
                    assert len(popped_from_stack) == 1, f"only one item was supposed to be popped but found a different number: {popped_from_stack}"
                    assert type(popped_from_stack[0]) is Node, f"was supposed to pop a node but instead popped: {popped_from_stack[0]}"
                    assert popped_from_stack[0].operation != 'NONE', f"popped node was supposed to have an operation but did not: {popped_from_stack[0]}"
                    new_node.operation = popped_from_stack[0].operation
                    new_node.parameters = popped_from_stack[0].parameters
                else:
                    new_node.operation = push_token.operation
                    if push_token.operation == 'epsilon':
                        new_node.parameters = ['&']
                    else:
                        new_node.parameters = popped_from_stack
                assert new_node.operation != 'NONE', f"trying to push malformed node to stack - no operation"
                assert new_node.parameters != [], f"trying to push malformed node to stack - no parameters"
                stack.append(new_node)
            else:
                assert popped_from_input != "", f"was supposed to push the value from input but nothing was popped from input"
                stack.append(popped_from_input)

            a_rule_was_followed = True
            break
        if not a_rule_was_followed:
            # if we are at the end of the input and there is only one token left in the stack (it has to be a Node) then return that node
            if len(stack) == 2:
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