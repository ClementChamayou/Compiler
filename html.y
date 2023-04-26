%{

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <ctype.h>

extern int yylex();
extern int yyparse();
extern FILE* yyin;

void yyerror(const char* s);
void process_hx(int tag_level, char* words);

#ifdef YYDEBUG
  yydebug = 1;
#endif

%}

%union {
    char * strval;
    int ival;
}

%token TOK_HTMLO TOK_HTMLC TOK_HEADO TOK_HEADC TOK_BODYO TOK_BODYC TOK_TITLEO TOK_TITLEC
%token TOK_STO TOK_STC
%token TOK_PO TOK_PC
%token TOK_STRING

%type <strval> text
%type <strval> TOK_STRING
%type <ival> TOK_STO

%%

html : TOK_HTMLO head body TOK_HTMLC

head : TOK_HEADO title TOK_HEADC

title : TOK_TITLEO text TOK_TITLEC

body : TOK_BODYO elements TOK_BODYC

elements : element elements
        | /* End */
        ;

element : hX
        | paragraph
        ;

hX : TOK_STO text TOK_STC
     {process_hx($1, $2);}

paragraph : TOK_PO text TOK_PC

text: TOK_STRING
    {$$ = $1;}
%%

int hx_count[6] = {0};
int hx_total_length[6] = {0};
int hx_hierarchy[6] = {0};

int count_words(const char *str) {
    int count = 0;
    int in_word = 0;

    while (*str) {
        if (isspace((unsigned char)*str)) {
            in_word = 0;
        } else {
            count += !in_word;
            in_word = 1;
        }
        str++;
    }

    return count;
}

void process_hx(int tag_level, char * words){
    int word_count = count_words(words);
    hx_count[tag_level - 1]++;
    hx_total_length[tag_level - 1] += word_count;
    printf("h%d %s: %d words\n", tag_level, words, word_count);

    hx_hierarchy[tag_level - 1]++;

    for (int i = tag_level; i < 6; i++) {
        hx_hierarchy[i] = 0;
    }

    FILE *toc_file = fopen("table_content.txt", "a");

    for (int i = 0; i < tag_level - 1; i++) {
        fprintf(toc_file, "    ");
    }

    for (int i = 0; i < tag_level - 1; i++) {
        fprintf(toc_file, "%d.", hx_hierarchy[i]);
    }

    fprintf(toc_file, "%d- %s\n", hx_hierarchy[tag_level - 1], words);

    fclose(toc_file);
}

int main() {
    yyin = fopen("test.html", "r");

    if (!yyin){
        printf("File does not exist or didn't open properly");
        return 0;
    }

    // Clear the table_content.txt file before writing
    FILE *toc_file = fopen("table_content.txt", "w");
    fclose(toc_file);

    do {
        yyparse();
    } while(!feof(yyin));

    fclose(yyin);

    // Statistics on the headings
    printf("\nStatistics on headings\n--------------\n");
    for (int i = 0; i < 6; i++) {
        if (hx_count[i] > 0) {
            double average_length = (double)hx_total_length[i] / (double)hx_count[i];
            printf("h%d: count=%d, average_length=%.2f\n", i + 1, hx_count[i], average_length);
        }
    }

    return 0;
}

void yyerror(const char* s) {
    fprintf(stderr, "Parse error: %s\n", s);
    exit(1);
}