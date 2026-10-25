// SPDX-License-Identifier: MIT
// No models or GPU: validate real parser depth boundaries and recovery after rejection.
#include "llama-grammar.h"
#include "jinja/runtime.h"
#include "json.h"
#include <iostream>
#include <stdexcept>
int main(){
    int cases=0;
    for(int n:{0,16,256,300}){
        std::string s="root ::= "+std::string(n,'(')+"\"x\""+std::string(n,')');
        llama_grammar_parser parser;bool ok=false;try{ok=parser.parse(s.c_str());}catch(const std::exception &){}
        if(ok!=(n<=256))throw std::runtime_error("grammar depth boundary failed");++cases;
    }
    for(int n:{0,16,128,129,300}){
        common_json value=0;for(int i=0;i<n;++i)value=common_json::array({value});
        common_json obj=common_json::object();obj["input"]=value;bool ok=true;
        try{jinja::context ctx;jinja::global_from_json(ctx,obj,true);}catch(const std::exception &){ok=false;}
        if(ok!=(n<=128))throw std::runtime_error("JSON depth boundary failed");++cases;
    }
    llama_grammar_parser recovered;if(!recovered.parse("root ::= \"x\""))return 2;
    std::cout<<"PASS "<<cases+1<<" actual grammar/JSON boundary and recovery cases; no model/GPU"<<std::endl;
}
