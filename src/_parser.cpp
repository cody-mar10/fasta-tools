#include "_parser.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <iterator>

// Parser public methods

/* 
Return the next FASTA record
*/
Record Parser::next() {
    return Record(this->file, this->line);
}

/*
Take all records from the file.
*/
Records Parser::all() {
    Records records;

    while (this->has_next()) {
        records.push_back(this->next());
    }

    return records;
}

/*
Take `n` records from the front of the file.
*/
Records Parser::take(size_t n) {
    Records records;
    records.reserve(n);

    for (size_t i = 0; i < n; i++) {
        if (!this->has_next()) {
            break;
        }
        records.push_back(this->next());
    }

    return records;
}

/*
Refresh the file stream to read from the beginning again.
*/
void Parser::refresh() {
    this->file.clear();
    this->file.seekg(0);
    this->init_line();
}