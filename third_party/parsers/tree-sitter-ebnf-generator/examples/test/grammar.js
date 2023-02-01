// This file was autogenerated by parse_grammar.lua from test.ebnf.

/*
 * inline constants: 
 */

module.exports = grammar({
  name: 'test',

  rules: {
    /*
     * test.ebnf:2 
     * Foo ::= ValDcl | ValDef
     */
    Foo: $ => choice($.ValDcl, $.ValDef),
    /*
     * test.ebnf:3 
     * id ::= [a-zA-Z0-9]+
     */
    _id: $ => repeat1(/[a-zA-Z0-9]/),
    /*
     * test.ebnf:4 
     * type ::= id
     */
    _type: $ => $._id,
    /*
     * test.ebnf:5 
     * ValDcl ::= 'val' id ':' id
     */
    ValDcl: $ => seq('val', $._id, ':', $._id),
    /*
     * test.ebnf:6 
     * ValDef ::= 'val' id (':' id)? '=' id
     */
    ValDef: $ => seq('val', $._id, optional(seq(':', $._id)), '=', $._id)
  }
});