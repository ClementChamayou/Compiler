from collections import defaultdict
import re
import os

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def splitGrammar(grammar):
    terminal_symbols = set()
    non_terminal_symbols = set()

    # Remove newline characters and split the grammar string by '::='
    production_rules = [rule.strip() for rule in grammar.split('\n') if rule.strip()]

    for rule in production_rules:
        lhs, rhs = rule.split('::=')
        lhs = lhs.strip()
        non_terminal_symbols.add(lhs)
        rhs_symbols = rhs.split()
        
        for symbol in rhs_symbols:
            if symbol != "ε" and symbol not in non_terminal_symbols:
                terminal_symbols.add(symbol)

    # Remove non-terminal symbols from the terminal symbols set
    terminal_symbols = terminal_symbols - non_terminal_symbols
    
    # Convert the sets to lists and return them
    return list(terminal_symbols), list(non_terminal_symbols)

def grammar_to_dict(grammar_string, non_terminal_symbols):
    grammar_dict = {}
    production_rules = [rule.strip() for rule in grammar_string.split('\n') if rule.strip()]
    first_flag = 0

    for non_terminal in non_terminal_symbols:
        grammar_dict[non_terminal] = []

    for rule in production_rules:
        lhs, rhs = rule.split('::=')
        lhs = lhs.strip()
        rhs = rhs.split('|')  # Split the right-hand side using the '|' symbol
        if (not first_flag):
            first_non_terminal_symbol = lhs
            first_flag = 1

        for r in rhs:
            grammar_dict[lhs].append(r.strip().split())

    return grammar_dict, first_non_terminal_symbol

def compute_FIRST(grammar, terminal_symbols, non_terminal_symbols):
    FIRST = defaultdict(set)

    def first(symbol):
        if symbol == "ε":
            return {"ε"}
        if symbol in FIRST:
            return FIRST[symbol]
        if symbol in terminal_symbols:
            return {symbol}
        for production in grammar[symbol]:
            first_set = set()
            for prod_symbol in production:
                symbol_first = first(prod_symbol)
                first_set.update(symbol_first - {"ε"})
                if "ε" not in symbol_first:
                    break
            else:
                first_set.add("ε")
            FIRST[symbol].update(first_set)
        return FIRST[symbol]

    for symbol in non_terminal_symbols:
        first(symbol)

    return FIRST

def print_FIRST_sets(FIRST_sets):
    print("FIRST sets:")
    for symbol, first_set in FIRST_sets.items():
        formatted_set = ', '.join(sorted(first_set))
        print(f"FIRST({symbol}) = {{{formatted_set}}}")

def compute_FOLLOW(grammar, non_terminal_symbols, FIRST, first_non_terminal):
    FOLLOW = defaultdict(set)

    # Rule 1: Start symbol should have '$' in its FOLLOW set
    start_symbol = first_non_terminal
    FOLLOW[start_symbol].add('$')

    def follow(symbol):
        if symbol in terminal_symbols:
            return set()

        # If FOLLOW set is already computed, return it
        if symbol in computed_follow:
            return FOLLOW[symbol]

        computed_follow.add(symbol)
        for lhs, rhs in grammar.items():
            for production in rhs:
                if symbol in production:
                    idx = production.index(symbol)
                    if idx + 1 < len(production):
                        beta = production[idx + 1]
                        # Rule 2: Add FIRST(beta) - {"ε"} to FOLLOW(symbol)
                        if beta not in terminal_symbols:
                            FOLLOW[symbol].update(FIRST[beta] - {"ε"})
                        else:
                            FOLLOW[symbol].update({beta})
                        # Rule 3: If "ε" in FIRST(beta), add FOLLOW(lhs) to FOLLOW(symbol)
                        if "ε" in FIRST[beta]:
                            FOLLOW[symbol].update(follow(lhs))
                    else:
                        # Rule 3: If the symbol is at the end of the production, add FOLLOW(lhs) to FOLLOW(symbol)
                        FOLLOW[symbol].update(follow(lhs))

        return FOLLOW[symbol]

    computed_follow = set()
    for symbol in non_terminal_symbols:
        follow(symbol)

    return FOLLOW

def print_FOLLOW_sets(FOLLOW_sets):
    print("FOLLOW sets:")
    for symbol, follow_set in FOLLOW_sets.items():
        formatted_set = ', '.join(sorted(follow_set))
        print(f"FOLLOW({symbol}) = {{{formatted_set}}}")

def generate_predictive_parsing_table(grammar, FIRST, FOLLOW):
    parsing_table = defaultdict(dict)

    for non_terminal, productions in grammar.items():
        for production in productions:
            first_of_production = FIRST[production[0]] if production[0] in non_terminal_symbols else {production[0]}

            # Rule 1: For every terminal a in FIRST(α), add A -> α to M[A, a]
            for terminal in first_of_production - {"ε"}:
                parsing_table[(non_terminal, terminal)] = production

            # Rule 2 and 3: If "ε" belongs to FIRST(α), then for every terminal b in FOLLOW(A), add A -> α to M[A, b]
            if "ε" in first_of_production:
                for terminal in FOLLOW[non_terminal]:
                    parsing_table[(non_terminal, terminal)] = production

    return parsing_table

def print_tables_to_html(grammar, table, terminal_symbols, FIRST, FOLLOW, file_name="tables.html"):
    ordered_non_terminals = list(grammar.keys())
    
    with open(file_name, "w") as f:
        f.write("<!DOCTYPE html>\n<html>\n<head>\n<style>\n")
        f.write("body {font-family: 'Calibri', sans-serif;}\n")  # Set font to Calibri
        f.write("table {border-collapse: collapse;width: 100%;}\n")
        f.write("th, td {border: 1px solid black;text-align: center;padding: 8px;}\n")
        f.write("th {background-color: #f2f2f2;}\n</style>\n</head>\n<body>\n")
        
        # FIRST and FOLLOW sets table
        f.write("<table>\n")
        f.write("<tr>\n")
        f.write("<th>Non-Terminal</th>\n")
        f.write("<th>FIRST</th>\n")
        f.write("<th>FOLLOW</th>\n</tr>\n")
        
        for non_terminal in ordered_non_terminals:
            f.write("<tr>\n")
            f.write(f"<td>{non_terminal}</td>\n")
            f.write(f"<td>{{ {', '.join(sorted(FIRST[non_terminal]))} }}</td>\n")
            f.write(f"<td>{{ {', '.join(sorted(FOLLOW[non_terminal]))} }}</td>\n")
            f.write("</tr>\n")
        
        f.write("</table>\n")
        f.write("<br>\n")  # Add a line break between tables
        
        # Predictive parsing table
        f.write("<table>\n")
        f.write("<tr>\n<th></th>\n")
        
        for t in terminal_symbols:
            f.write(f"<th>{t}</th>\n")
        f.write("</tr>\n")
        
        for non_terminal in ordered_non_terminals:
            f.write("<tr>\n")
            f.write(f"<td>{non_terminal}</td>\n")
            for t in terminal_symbols:
                if (non_terminal, t) in table:
                    f.write(f"<td>{non_terminal} ::= {' '.join(table[(non_terminal, t)])}</td>\n")
                else:
                    f.write("<td></td>\n")
            f.write("</tr>\n")
        
        f.write("</table>\n</body>\n</html>")

def predictive_parser(w, parsing_table, start_symbol, terminal_symbols):
    w[-1] = ("$", "EOF")
    ip = 0  # input pointer
    stack = ["$", start_symbol]

    derivation = []

    in_hx = False
    hx_open_value = None
    words = ""
    hx_count = [0] * 6 # track the number of heading for each category
    hx_total_length = [0] * 6 # total number of words per type of headings
    hx_hierarchy = [0] * 6
    
    while stack:
        X = stack[-1]  # top stack symbol
        a = w[ip][0]  # symbol pointed to by ip
        current_value = w[ip][1]

        # If X is a terminal or $
        if X in terminal_symbols or X == "$":
            if X == a:
                stack.pop()
                ip += 1

                if a.startswith("HX_OPEN"):

                    in_hx = True
                    hx_open_value = current_value
                    hx_count[tag_level(current_value)-1] += 1

                elif a.startswith("HX_CLOSE"):

                    in_hx = False
                    hx_level = tag_level(hx_open_value)
                    word_count = len(words.split())
                    hx_hierarchy[hx_level-1] += 1
                    hx_hierarchy = hierarchy(hx_hierarchy, hx_level, words)
                    hx_total_length[hx_level-1] += word_count
                    print(f"<h{hx_level}> {words} --> {word_count} words")
                    words = ""

                elif a == "WORD" and in_hx:
                    words += " " + current_value
            else:
                return f"Error first if for {X} - {a}"  # Mismatch between input symbol and expected terminal symbol
        else:  # X is a non-terminal
            if (X, a) in parsing_table:
                production = parsing_table[(X, a)]
                stack.pop()

                # Push the right-hand side symbols in reverse order in the stack
                for symbol in production[::-1]:
                    if symbol != "ε":
                        stack.append(symbol)
                # Outputs the production
                derivation.append(f"{X} -> {' '.join(production)}")
            else:
                return f"Error for {X} - {a}"  # Input symbol cannot be derived using the current grammar

    if ip != len(w):
        return "Final error"

    return derivation, hx_count, hx_total_length

def tag_level(hx_tag):
    return int(hx_tag[-2])

def tokenize(text):

    tokens = []
    regex = re.compile(
        r"(?P<DOCTYPE><!DOCTYPE html>)|(?P<HTML_OPEN><html>)|(?P<HTML_CLOSE><\/html>)|(?P<HEAD_OPEN><head>)|(?P<HEAD_CLOSE><\/head>)|(?P<TITLE_OPEN><title>)|(?P<TITLE_CLOSE><\/title>)|(?P<BODY_OPEN><body>)|(?P<BODY_CLOSE><\/body>)|(?P<HX_OPEN><h[1-6]>)|(?P<HX_CLOSE><\/h[1-6]>)|(?P<POPEN><p>)|(?P<PCLOSE><\/p>)|(?P<WORD>\w+)"
    )

    matches = regex.finditer(text)

    for match in matches:
        for group_name, group_value in match.groupdict().items():
            if group_value is not None:
                tokens.append((group_name, group_value))
                break

    tokens.append(('EOF', 'EOF'))

    return tokens

def print_statistics(hx_count,hx_total_length):

    print("\nStatistics on headings")
    print("-" * 30)

    for i in range(6):
        if hx_count[i] > 0:
            average_length = hx_total_length[i] / hx_count[i]
            print(f"h{i + 1}: count={hx_count[i]}, average_length={average_length:.2f}")

def hierarchy(hx_hierarchy, hx_level, words, file_name="table_content.txt"):
    
    for i in range(hx_level, 6):
        hx_hierarchy[i] = 0

    with open(file_name, "a") as toc_file:
        for _ in range(hx_level - 1):
            toc_file.write("    ")

        for i in range(hx_level - 1):
            toc_file.write(f"{hx_hierarchy[i]}.")

        toc_file.write(f"{hx_hierarchy[hx_level - 1]}-{words}\n")

    return hx_hierarchy

if __name__ == "__main__":

    grammar_string = """
    html         ::= DOCTYPE html_element
    html_element ::= HTML_OPEN head body HTML_CLOSE
    head         ::= HEAD_OPEN title HEAD_CLOSE
    title        ::= TITLE_OPEN text TITLE_CLOSE
    body         ::= BODY_OPEN elements BODY_CLOSE
    elements     ::= element elements | ε
    element      ::= hx | p
    hx           ::= HX_OPEN text HX_CLOSE
    p            ::= POPEN text PCLOSE
    text         ::= WORD text | ε
    """
    output_file = "table_content.txt"
    
    if os.path.isfile(output_file):
        os.remove(output_file)
        print(f"Previous file \"{output_file}\" deleted.")

    tokens = tokenize(read_file("test.html"))
    #print(tokens)

    terminal_symbols, non_terminal_symbols = splitGrammar(grammar_string)
    grammar_dict, first_non_terminal = grammar_to_dict(grammar_string, non_terminal_symbols)

    #print(f"Grammar dict : \n{grammar_dict}")
    
    FIRST = compute_FIRST(grammar_dict,terminal_symbols, non_terminal_symbols)
    #print_FIRST_sets(FIRST)
    #print()

    FOLLOW = compute_FOLLOW(grammar_dict, non_terminal_symbols, FIRST, first_non_terminal)
    #print_FOLLOW_sets(FOLLOW)
    #print()

    parsing_table = generate_predictive_parsing_table(grammar_dict,FIRST,FOLLOW,)
    #print_tables_to_html(grammar_dict,parsing_table,terminal_symbols, FIRST, FOLLOW)

    derivation, hx_count, hx_total_length = predictive_parser(tokens, parsing_table, first_non_terminal, terminal_symbols)
   
    print_statistics(hx_count, hx_total_length)