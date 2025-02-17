type SearchResult = {
    caption: string;
    text: string;
    similarity: number;
};

type SearchResultsProps = {
    results: SearchResult[];
}

export default function SearchResults({ results }: SearchResultsProps) {
    console.log("*** top of SearchResults. ", results)
    return (
        <div>
            <h3>Search Results:</h3>
            {results.length === 0 ? (
                <p>No results found.</p>
            ) : (
                <ul>
                    {results.map((result, index) => (
                        <li key={index}>
                            <strong>{result.caption}</strong> (Similarity: {result.similarity.toFixed(2)})
                            <p>{result.text}</p>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}