export type SearchResult = {
    searchQuery: string;
    ragQuery: string;
    prompt: string;
    caption: string;
    text: string;
    similarity: number;
    // [segment id, document id, segment index, offset, length]
    record: [string, string, number, number, number];
};