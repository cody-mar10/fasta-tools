#include "_parser.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

// Parser public methods

Record Parser::next() {
    if (!this->has_next()) {
        return Record();
    }

    // remove > symbol from beginning of name
    // TODO: need to check if line is not empty?
    // technically that is done in the while loop
    // and the constructor requires the first line to start with >
    // BUG: if the header is just > without a name?
    std::string name{ std::move(this->line.substr(1)) };
    std::string seq{ "" };

    while (std::getline(this->file, this->line)) {
        if (this->line.empty()) {
            continue;
        }

        if (this->line[0] == '>') {
            break;
        }

        seq += this->line;
    }

    Record record(std::move(name), std::move(seq));

    return record;
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

void Parser::refresh() {
    this->file.clear();
    this->file.seekg(0);
    this->init_line();
}