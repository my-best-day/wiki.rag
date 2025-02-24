import { useState } from "react";
import { Box } from "@chakra-ui/react";
import SearchForm from "../components/SearchForm";
import SearchResults from "../components/SearchResults";
import { fetchSearchResults } from "../api/search";

import { SearchResult } from "../types/SearchResult";

type SearchResponse = {
    meta: {
        completed: string;
        received: string;
    };
    data: {
        results: SearchResult[];
        prompt: string;
        answer: string;
    };
};

export default function Home() {
    const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);

    const handleSearch = async (action: string, query: string, atLeast: number, threshold: number, atMost: number) => {
        try {
            const data = await fetchSearchResults(action, query, atLeast, threshold, atMost);
            console.log("*** in handleSearch, search results fetched: ", data);
            setSearchResponse(data);
        } catch (error) {
            console.error("Error fetching results", error);
        }
    };

    return (
        <Box>
            <SearchForm onSearch={handleSearch} />
            {searchResponse && (
                <SearchResults
                    results={searchResponse.data.results}
                    metadata={{
                        completed: searchResponse.meta.completed,
                        received: searchResponse.meta.received,
                        prompt: searchResponse.data.prompt,
                        answer: searchResponse.data.answer,
                    }}
                />
            )}
        </Box>
    );
}