import { useState } from "react";
import {
    Box,
    Button,
    Grid,
    GridItem,
    FormControl,
    FormLabel,
    Input,
    Textarea,
    Flex,
} from "@chakra-ui/react";

type SearchFormProps = {
    readonly onSearch: (query: string, atLeast: number, threshold: number, atMost: number) => void;
}

export default function SearchForm({ onSearch }: SearchFormProps) {
    const [query, setQuery] = useState("");
    const [atLeast, setAtLeast] = useState(3);
    const [threshold, setThreshold] = useState(0.6);
    const [atMost, setAtMost] = useState(5);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query, atLeast, threshold, atMost);
        }
    };

    return (
        <Flex w="100vw" justify="center" pt={4}>
            <Box maxW="600px" w="100%" p={4}>
                <form onSubmit={handleSearch}>
                    <FormControl mb={4}>
                        <FormLabel>Search Query</FormLabel>
                        <Textarea
                            value={query}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setQuery(e.target.value)}
                            placeholder="Enter search query..."
                            rows={4}
                        />
                    </FormControl>

                    <Button type="submit" colorScheme="blue" mb={4}>
                        Search!
                    </Button>

                    <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                        <GridItem>
                            <FormControl>
                                <FormLabel>At Least</FormLabel>
                                <Input
                                    type="number"
                                    value={atLeast}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setAtLeast(parseInt(e.target.value) || 3)
                                    }
                                    min={1}
                                    step={1}
                                />
                            </FormControl>
                        </GridItem>
                        <GridItem>
                            <FormControl>
                                <FormLabel>Threshold</FormLabel>
                                <Input
                                    type="number"
                                    value={threshold}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setThreshold(parseFloat(e.target.value) || 0.5)
                                    }
                                    min={0}
                                    max={1}
                                    step={0.05}
                                />
                            </FormControl>
                        </GridItem>
                        <GridItem>
                            <FormControl>
                                <FormLabel>At Most</FormLabel>
                                <Input
                                    type="number"
                                    value={atMost}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setAtMost(parseInt(e.target.value) || 5)
                                    }
                                    min={1}
                                    step={1}
                                />
                            </FormControl>
                        </GridItem>
                    </Grid>
                </form>
            </Box>
        </Flex>
    );
}