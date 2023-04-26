%option noyywrap
%option yylineno

%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define YY_DECL int yylex()

#include "html.tab.h"

%}

NUMBER     [1-6]
HTAGO      "<h"{NUMBER}">"
HTAGC      "</h"{NUMBER}">"

%%

{HTAGO} {
        sscanf(yytext, "<h%d>", &yylval.ival);
        //printf("Balise h%d\n", yylval.ival);
        return TOK_STO;
}

[ \t\n\r]+  {}
[^<]+       {yylval.strval = strdup(yytext);
             return TOK_STRING;}
"<html>"    {return TOK_HTMLO;}
"</html>"   {return TOK_HTMLC;}
"<head>"    {return TOK_HEADO;}
"</head>"   {return TOK_HEADC;}
"<title>"   {return TOK_TITLEO;}
"</title>"  {return TOK_TITLEC;}
"<body>"    {return TOK_BODYO;}
"</body>"   {return TOK_BODYC;}
"<p>"       {return TOK_PO;}
"</p>"      {return TOK_PC;}




{HTAGC} {
        return TOK_STC;
}

