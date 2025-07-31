"""
Result Aggregation Tool for combining and deduplicating results from multiple sources.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
from pydantic import Field

from agent_system.core import Tool, ToolConfig, ToolInputBase, ToolOutputBase, ToolExecutionError, register_tool


class ResultAggregationConfig(ToolConfig):
    """Configuration for result aggregation tool."""
    deduplication_method: str = Field(default="content_hash", description="Deduplication method: content_hash, title_similarity, or url_match")
    similarity_threshold: float = Field(default=0.85, description="Similarity threshold for deduplication (0-1)")
    max_results: int = Field(default=1000, description="Maximum number of results to return")
    prioritize_sources: List[str] = Field(default_factory=list, description="Sources to prioritize in ranking")
    merge_similar_results: bool = Field(default=True, description="Merge similar results instead of removing duplicates")


class ResultAggregationInput(ToolInputBase):
    """Input for result aggregation tool."""
    result_batches: List[Dict[str, Any]] = Field(..., description="List of result batches from different sources")
    aggregation_strategy: str = Field(default="merge_and_dedupe", description="Aggregation strategy: merge_and_dedupe, prioritize_sources, or simple_concat")
    ranking_criteria: List[str] = Field(default=["relevance", "recency", "authority"], description="Criteria for ranking results")


class ResultAggregationOutput(ToolOutputBase):
    """Output from result aggregation tool."""
    aggregated_results: List[Dict[str, Any]] = Field(..., description="Final aggregated and deduplicated results")
    total_input_results: int = Field(..., description="Total number of input results across all batches")
    total_output_results: int = Field(..., description="Number of results after aggregation and deduplication")
    duplicates_removed: int = Field(..., description="Number of duplicate results removed")
    results_merged: int = Field(..., description="Number of results that were merged")
    source_statistics: Dict[str, int] = Field(..., description="Statistics by source")
    aggregation_summary: str = Field(..., description="Summary of the aggregation process")


@register_tool(
    config_class=ResultAggregationConfig,
    input_class=ResultAggregationInput,
    output_class=ResultAggregationOutput,
    description="Aggregate and deduplicate results from multiple sources with intelligent merging"
)
class ResultAggregationTool(Tool[ResultAggregationConfig, ResultAggregationInput, ResultAggregationOutput]):
    """Tool for aggregating and deduplicating results from multiple sources."""
    
    def __init__(self, config: Optional[ResultAggregationConfig] = None, alias: Optional[str] = None):
        super().__init__(
            name="result_aggregation",
            short_description="Aggregate and deduplicate results from multiple sources",
            long_description="Intelligently combine, deduplicate, and rank results from multiple research sources with configurable strategies and similarity detection",
            config=config or ResultAggregationConfig(),
            alias=alias
        )
    
    @classmethod
    def _get_config_class(cls):
        return ResultAggregationConfig
    
    @classmethod
    def _get_input_class(cls):
        return ResultAggregationInput
    
    @classmethod
    def _get_output_class(cls):
        return ResultAggregationOutput
    
    def _execute(self, input_data: ResultAggregationInput, identity: Optional[Dict[str, Any]] = None) -> ResultAggregationOutput:
        """Execute result aggregation."""
        try:
            result_batches = input_data.result_batches
            aggregation_strategy = input_data.aggregation_strategy
            ranking_criteria = input_data.ranking_criteria
            
            if not result_batches:
                return ResultAggregationOutput(
                    aggregated_results=[],
                    total_input_results=0,
                    total_output_results=0,
                    duplicates_removed=0,
                    results_merged=0,
                    source_statistics={},
                    aggregation_summary="No result batches provided for aggregation"
                )
            
            # Flatten and standardize all results
            all_results = []
            source_stats = defaultdict(int)
            
            for batch in result_batches:
                batch_results = batch.get("results", [])
                batch_source = batch.get("source", "unknown")
                
                for result in batch_results:
                    standardized_result = self._standardize_result(result, batch_source)
                    all_results.append(standardized_result)
                    source_stats[batch_source] += 1
            
            total_input_results = len(all_results)
            
            if not all_results:
                return ResultAggregationOutput(
                    aggregated_results=[],
                    total_input_results=0,
                    total_output_results=0,
                    duplicates_removed=0,
                    results_merged=0,
                    source_statistics=dict(source_stats),
                    aggregation_summary="No results found in any batch"
                )
            
            # Apply aggregation strategy
            if aggregation_strategy == "merge_and_dedupe":
                aggregated_results, duplicates_removed, merged_count = self._merge_and_deduplicate(all_results)
            elif aggregation_strategy == "prioritize_sources":
                aggregated_results, duplicates_removed, merged_count = self._prioritize_sources(all_results)
            elif aggregation_strategy == "simple_concat":
                aggregated_results, duplicates_removed, merged_count = self._simple_concatenation(all_results)
            else:
                # Default to merge_and_dedupe
                aggregated_results, duplicates_removed, merged_count = self._merge_and_deduplicate(all_results)
            
            # Apply ranking
            aggregated_results = self._rank_results(aggregated_results, ranking_criteria)
            
            # Limit results
            if len(aggregated_results) > self.config.max_results:
                aggregated_results = aggregated_results[:self.config.max_results]
            
            total_output_results = len(aggregated_results)
            
            # Generate summary
            aggregation_summary = self._generate_aggregation_summary(
                total_input_results, total_output_results, duplicates_removed, 
                merged_count, dict(source_stats), aggregation_strategy
            )
            
            return ResultAggregationOutput(
                aggregated_results=aggregated_results,
                total_input_results=total_input_results,
                total_output_results=total_output_results,
                duplicates_removed=duplicates_removed,
                results_merged=merged_count,
                source_statistics=dict(source_stats),
                aggregation_summary=aggregation_summary
            )
            
        except Exception as e:
            raise ToolExecutionError(f"Result aggregation failed: {str(e)}")
    
    def _standardize_result(self, result: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Standardize a result to a common format."""
        standardized = {
            "title": result.get("title", result.get("name", "Untitled")),
            "content": result.get("content", result.get("description", result.get("summary", ""))),
            "url": result.get("url", result.get("link", "")),
            "source": result.get("source", source),
            "relevance_score": float(result.get("relevance_score", result.get("score", 0.5))),
            "date": result.get("date", result.get("timestamp", "")),
            "author": result.get("author", ""),
            "tags": result.get("tags", []),
            "metadata": result.get("metadata", {}),
            "original_data": result  # Keep original for reference
        }
        
        # Generate content hash for deduplication
        content_for_hash = f"{standardized['title']}{standardized['content']}{standardized['url']}"
        standardized["content_hash"] = hashlib.md5(content_for_hash.encode()).hexdigest()
        
        return standardized
    
    def _merge_and_deduplicate(self, results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Merge and deduplicate results using configured method."""
        if self.config.deduplication_method == "content_hash":
            return self._deduplicate_by_hash(results)
        elif self.config.deduplication_method == "title_similarity":
            return self._deduplicate_by_similarity(results)
        elif self.config.deduplication_method == "url_match":
            return self._deduplicate_by_url(results)
        else:
            return self._deduplicate_by_hash(results)
    
    def _deduplicate_by_hash(self, results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Deduplicate by content hash."""
        seen_hashes = set()
        unique_results = []
        duplicates_removed = 0
        merged_count = 0
        
        for result in results:
            content_hash = result["content_hash"]
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(result)
            else:
                duplicates_removed += 1
                
                # If merge_similar_results is enabled, merge with existing
                if self.config.merge_similar_results:
                    existing_result = next(r for r in unique_results if r["content_hash"] == content_hash)
                    merged_result = self._merge_results(existing_result, result)
                    
                    # Replace existing result with merged version
                    for i, r in enumerate(unique_results):
                        if r["content_hash"] == content_hash:
                            unique_results[i] = merged_result
                            merged_count += 1
                            break
        
        return unique_results, duplicates_removed, merged_count
    
    def _deduplicate_by_similarity(self, results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Deduplicate by title similarity."""
        unique_results = []
        duplicates_removed = 0
        merged_count = 0
        
        for result in results:
            similar_result = None
            max_similarity = 0
            
            # Find most similar existing result
            for existing in unique_results:
                similarity = self._calculate_similarity(result["title"], existing["title"])
                if similarity > max_similarity and similarity >= self.config.similarity_threshold:
                    max_similarity = similarity
                    similar_result = existing
            
            if similar_result is None:
                # No similar result found, add as new
                unique_results.append(result)
            else:
                # Similar result found
                duplicates_removed += 1
                
                if self.config.merge_similar_results:
                    # Merge with similar result
                    merged_result = self._merge_results(similar_result, result)
                    
                    # Replace similar result with merged version
                    for i, r in enumerate(unique_results):
                        if r is similar_result:
                            unique_results[i] = merged_result
                            merged_count += 1
                            break
        
        return unique_results, duplicates_removed, merged_count
    
    def _deduplicate_by_url(self, results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Deduplicate by URL matching."""
        seen_urls = set()
        unique_results = []
        duplicates_removed = 0
        merged_count = 0
        
        for result in results:
            url = result["url"].strip() if result["url"] else ""
            
            # Normalize URL for comparison
            normalized_url = self._normalize_url(url)
            
            if not url or normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
            else:
                duplicates_removed += 1
                
                if self.config.merge_similar_results:
                    # Find existing result with same URL and merge
                    existing_result = next(
                        r for r in unique_results 
                        if self._normalize_url(r["url"]) == normalized_url
                    )
                    merged_result = self._merge_results(existing_result, result)
                    
                    # Replace existing result
                    for i, r in enumerate(unique_results):
                        if self._normalize_url(r["url"]) == normalized_url:
                            unique_results[i] = merged_result
                            merged_count += 1
                            break
        
        return unique_results, duplicates_removed, merged_count
    
    def _prioritize_sources(self, results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Aggregate with source prioritization."""
        # First deduplicate
        deduplicated_results, duplicates_removed, merged_count = self._merge_and_deduplicate(results)
        
        # Then sort by source priority
        priority_sources = self.config.prioritize_sources
        
        def source_priority(result):
            source = result["source"]
            try:
                return priority_sources.index(source)
            except ValueError:
                return len(priority_sources)  # Lower priority for unlisted sources
        
        deduplicated_results.sort(key=source_priority)
        
        return deduplicated_results, duplicates_removed, merged_count
    
    def _simple_concatenation(self, results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Simple concatenation without deduplication."""
        return results, 0, 0
    
    def _merge_results(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two similar results into one comprehensive result."""
        merged = result1.copy()
        
        # Use the result with higher relevance score as base
        if result2["relevance_score"] > result1["relevance_score"]:
            merged = result2.copy()
            result1, result2 = result2, result1
        
        # Merge content (take longer version)
        if len(result2["content"]) > len(merged["content"]):
            merged["content"] = result2["content"]
        
        # Merge tags
        merged_tags = list(set(merged["tags"] + result2["tags"]))
        merged["tags"] = merged_tags
        
        # Update metadata
        merged["metadata"]["merged_sources"] = [result1["source"], result2["source"]]
        merged["metadata"]["merged_count"] = merged["metadata"].get("merged_count", 1) + 1
        
        # Use more recent date if available
        if result2["date"] and (not merged["date"] or result2["date"] > merged["date"]):
            merged["date"] = result2["date"]
        
        # Average relevance scores
        merged["relevance_score"] = (result1["relevance_score"] + result2["relevance_score"]) / 2
        
        return merged
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        if not url:
            return ""
        
        # Remove common variations
        url = url.lower().strip()
        url = url.rstrip('/')
        
        # Remove common tracking parameters
        if '?' in url:
            base_url = url.split('?')[0]
            return base_url
        
        return url
    
    def _rank_results(self, results: List[Dict[str, Any]], criteria: List[str]) -> List[Dict[str, Any]]:
        """Rank results based on specified criteria."""
        def ranking_score(result):
            score = 0
            
            for criterion in criteria:
                if criterion == "relevance":
                    score += result["relevance_score"] * 0.4
                elif criterion == "recency":
                    # Simple recency boost for results with dates
                    if result["date"]:
                        score += 0.2  # Boost for having a date
                elif criterion == "authority":
                    # Boost for known authoritative sources
                    if result["source"] in self.config.prioritize_sources:
                        score += 0.3
                elif criterion == "completeness":
                    # Boost for complete results
                    completeness = sum([
                        1 if result["title"] else 0,
                        1 if result["content"] else 0,
                        1 if result["url"] else 0,
                        1 if result["author"] else 0
                    ]) / 4
                    score += completeness * 0.1
            
            return score
        
        results.sort(key=ranking_score, reverse=True)
        return results
    
    def _generate_aggregation_summary(self, total_input: int, total_output: int, 
                                    duplicates_removed: int, merged_count: int,
                                    source_stats: Dict[str, int], strategy: str) -> str:
        """Generate a summary of the aggregation process."""
        summary_parts = []
        
        summary_parts.append(f"Aggregation completed using '{strategy}' strategy")
        summary_parts.append(f"Input: {total_input} results from {len(source_stats)} sources")
        summary_parts.append(f"Output: {total_output} aggregated results")
        
        if duplicates_removed > 0:
            summary_parts.append(f"Duplicates removed: {duplicates_removed} ({(duplicates_removed/total_input)*100:.1f}%)")
        
        if merged_count > 0:
            summary_parts.append(f"Results merged: {merged_count}")
        
        if source_stats:
            summary_parts.append("Source distribution:")
            for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"  - {source}: {count} results")
        
        reduction_percent = ((total_input - total_output) / total_input) * 100 if total_input > 0 else 0
        if reduction_percent > 0:
            summary_parts.append(f"Overall reduction: {reduction_percent:.1f}%")
        
        return "\n".join(summary_parts)