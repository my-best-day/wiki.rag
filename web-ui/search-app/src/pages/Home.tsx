import { useState } from "react";
import SearchForm from "../components/SearchForm";
import SearchResults from "../components/SearchResults";
import { fetchSearchResults } from "../api/search";

export default function Home() {
    const [results, setResults] = useState([]);

    const handleSearch = async (
        query: string,
        atLeast: number,
        threshold: number,
        atMost: number
    ) => {
        try {
            const data = await fetchSearchResults(query, atLeast, threshold, atMost);
            const results = data.data.results;
            console.log("*** in handleSearch, search results fetched: ", results)
            setResults(results || []);
        } catch (error) {
            console.error("Error fetching results", error);
        }
    };

    return (
        <div>
            <h1>Search App</h1>
            <SearchForm onSearch={handleSearch} />
            <SearchResults results={results} />
        </div>
    )
}