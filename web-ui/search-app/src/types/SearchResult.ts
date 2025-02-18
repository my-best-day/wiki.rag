export type SearchResult = {
    caption: string;
    text: string;
    similarity: number;
    // [segment id, document id, segment index, offset, length]
    record: [string, string, number, number, number];
};