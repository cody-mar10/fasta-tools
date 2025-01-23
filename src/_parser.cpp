#include "_parser.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <iterator>
#include <filesystem>

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
    this->refresh();

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

/*
Return the file extension based on the record types.
*/
std::string Parser::extension() {
    switch (this->type) {
        case RecordType::GENOME:
            return ".fna";
        case RecordType::GENE:
            return ".ffn";
        case RecordType::PROTEIN:
            return ".faa";
        default:
            return ".fasta";
    }
}

/*
Return the next header in the file.
*/
// TODO: some kind of bug that only returns the first header over and over
// also propagates into counting number of seqs...
Header Parser::next_header() {
    // advance to the next header
    if ((this->line.empty()) || (this->line[0] != '>')) {
        while (std::getline(this->file, this->line)) {
            if (this->line.empty()) {
                continue;
            }

            if (this->line[0] == '>') {
                break;
            }
        }
    }

    // for some reason the move doesn't clear the line...
    Header header(std::move(this->line));
    this->line.clear();

    return header;
}

/*
Return all headers in the file.
*/
Headers Parser::headers() {
    this->refresh();

    Headers headers;

    while (this->has_next()) {
        Header header = this->next_header();
        if (header.empty()) {
            break;
        }
        headers.push_back(header);
    }

    return headers;
}


/*
Get the number of sequences in the file. Refreshes the parser to point to the beginning of the file.
*/
size_t Parser::count() {
    this->refresh();
    size_t n = 0;

    while (this->has_next()) {
        Header header = this->next_header();
        if (header.empty()) {
            break;
        }
        n++;
    }

    this->refresh();
    return n;
}

// Parser private methods

void Parser::detect_format(const std::string& filename) {
    // First, try to resolve from the file extension
    namespace fs = std::filesystem;
    
     // First, try to resolve from the file extension
    fs::path path(filename);
    std::string ext = path.extension().string();
    if (!(ext.empty())) {
        
        // could be zipped, check 2nd char since 1st is a .
        if (ext[1] != 'f') {
            ext = path.stem().extension().string();
        }

        if (ext == ".fna") {
            this->type = RecordType::GENOME;
            return;
        }
        else if (ext == ".ffn") {
            this->type = RecordType::GENE;
            return;
        }
        else if (ext == ".faa") {
            this->type = RecordType::PROTEIN;
            return;
        }
    }

    // If the extension is not recognized, we will try to guess from the first 5 records.
    Records records = this->take(5);

    size_t genome_count = 0;
    size_t gene_count = 0;
    for (const Record& record : records) {
        /* 
        The record object autodetects the type when passing the file stream, which is how 
        Parser::take (and Parser::next) work.
        One challenge is distinguishing genomes from genes, since we set an arbitrary length 
        cutoff of 5kb. However, there could be genes that large, which is why we will consider the
        first 5 records and take the most common type.
        
        However, if there is a protein sequence, we will default to that.
        */

        switch (record.type) {
            case RecordType::GENOME:
                genome_count++;
                break;
            case RecordType::GENE:
                gene_count++;
                break;
            case RecordType::PROTEIN:
                this->type = RecordType::PROTEIN;
                return;
            default:
                break;
        }
    }

    // only get here if nucleotide sequences
    if (genome_count > gene_count) {
        this->type = RecordType::GENOME;
    }
    else if (gene_count > genome_count) {
        this->type = RecordType::GENE;
    } else {
        // default to nucleotide since we can't tell
        this->type = RecordType::NUCLEOTIDE;
    }

    this->refresh();
}