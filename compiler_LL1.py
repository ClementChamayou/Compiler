import re
import os

def tokenize(text):
    tokens = []
    regex = re.compile(
        r"(?P<DOCTYPE><!DOCTYPE html>)|(?P<HTML_OPEN><html>)|(?P<HTML_CLOSE><\/html>)|(?P<HEAD_OPEN><head>)|(?P<HEAD_CLOSE><\/head>)|(?P<TITLE_OPEN><title>)|(?P<TITLE_CLOSE><\/title>)|(?P<BODY_OPEN><body>)|(?P<BODY_CLOSE><\/body>)|(?P<HX_OPEN><h[1-6]>)|(?P<HX_CLOSE><\/h[1-6]>)|(?P<P_OPEN><p>)|(?P<P_CLOSE><\/p>)|(?P<WORD>\w+)"
    )
    matches = regex.finditer(text)
    for match in matches:
        for group_name, group_value in match.groupdict().items():
            if group_value is not None:
                tokens.append((group_name, group_value))
                break
    tokens.append(('EOF', 'EOF'))
    return tokens

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

class RecursiveDescentParser:
    def __init__(self, tokens, file_name):
        self.tokens = tokens
        self.pos = 0
        self.hx_count = [0] * 6
        self.hx_total_length = [0] * 6
        self.hx_hierarchy = [0] * 6
        self.file_name = file_name

    def lookahead(self):
        return self.tokens[self.pos]

    def consume(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def match(self, token_type):
        if self.lookahead()[0] == token_type:
            self.pos +=1
        else:
            raise Exception(f"Syntax error: expected {token_type}, but found {self.lookahead()[0]} {self.lookahead()[1]}")

    def html(self):
        self.match('DOCTYPE')
        self.match('HTML_OPEN')
        self.head()
        self.body()
        self.match('HTML_CLOSE')

    def head(self):
        self.match('HEAD_OPEN')
        self.title()
        self.match('HEAD_CLOSE')

    def title(self):
        self.match('TITLE_OPEN')
        self.text()
        self.match('TITLE_CLOSE')

    def body(self):
        self.match('BODY_OPEN')
        self.elements()
        self.match('BODY_CLOSE')

    def elements(self):
        if self.lookahead()[0] is None:
            return

        if self.lookahead()[0] == 'HX_OPEN':
            self.hx()
            self.elements()
        elif self.lookahead()[0] == 'P_OPEN':
            self.p()
            self.elements()
        else:
            return

    def element(self):
        if self.lookahead()[0] in ('H1_OPEN', 'H2_OPEN', 'H3_OPEN', 'H4_OPEN', 'H5_OPEN', 'H6_OPEN'):
            self.hx()
        elif self.lookahead()[0] == 'P_OPEN':
            self.p()

    
    def process_hx(self, tag_level, words ,word_count):
        
        self.hx_count[tag_level - 1] += 1
        self.hx_total_length[tag_level - 1] += word_count

        self.hx_hierarchy[tag_level - 1] += 1
        for i in range(tag_level, 6):
            self.hx_hierarchy[i] = 0

        with open(self.file_name, "a") as toc_file:
            for _ in range(tag_level - 1):
                toc_file.write("    ")

            for i in range(tag_level - 1):
                toc_file.write(f"{self.hx_hierarchy[i]}.")

            toc_file.write(f"{self.hx_hierarchy[tag_level - 1]}- {words}\n")
        print(f"<h{tag_level}> {words} --> {word_count} words")

    def hx(self):
        hx_open_tag = self.lookahead()[0]
        hx_level = int(self.lookahead()[1][-2])  # Extract the heading level (1-6)
        self.match(hx_open_tag)
        hx_text, word_count = self.text()
        self.match(hx_open_tag.replace('_OPEN', '_CLOSE'))

        self.process_hx(hx_level, hx_text, word_count)

    
    def p(self):
        self.match('P_OPEN')
        self.text()
        self.match('P_CLOSE')

    def text(self):
        text = []
        while self.lookahead()[0] == 'WORD':
            text.append(self.consume()[1])
        return ' '.join(text), len(text)

    def print_statistics(self):
        print("\nStatistics on headings")
        print("--------------")
        for i in range(6):
            if self.hx_count[i] > 0:
                average_length = self.hx_total_length[i] / self.hx_count[i]
                print(f"h{i + 1}: count={self.hx_count[i]}, average_length={average_length:.2f}")

if __name__ == "__main__":

    input_file = "test.html"
    output_file = "table_content.txt"

    if os.path.isfile(output_file):
        os.remove(output_file)
        print(f"Previous file \"{output_file}\" deleted.")

    text = read_file(input_file)
    tokens = tokenize(text)
    
    parser = RecursiveDescentParser(tokens, output_file)
    parser.html()
    parser.print_statistics()

    print(f"Outline written to {output_file}.")