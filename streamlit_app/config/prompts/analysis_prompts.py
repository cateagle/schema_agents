"""
Result analysis and interpretation prompts.
"""

RESULT_INTERPRETATION_PROMPT = """
You are an expert research analyst. Analyze these search results and provide insights.

Search Query: {query}
Schema Used: {schema}
Results: {results}

Please provide:
1. **Summary**: Key findings and patterns
2. **Quality Assessment**: Reliability and completeness
3. **Insights**: Important trends or discoveries
4. **Recommendations**: Suggestions for further research

Be thorough but concise. Focus on actionable insights.
"""

RESEARCH_SUMMARY_PROMPT = """
Create a comprehensive summary of this research session:

Research Topic: {topic}
Total Results: {total_results}
Agents Used: {agent_count}
Execution Time: {execution_time}

Key Findings:
{findings}

Provide:
1. Executive summary (2-3 sentences)
2. Main insights discovered
3. Data quality assessment
4. Suggested next steps
"""

QUALITY_ASSESSMENT_PROMPT = """
Assess the quality of these research results:

Schema: {schema}
Results: {results}

Evaluate:
1. **Completeness**: How well do results match the schema?
2. **Accuracy**: Are the results reliable and well-sourced?
3. **Relevance**: How relevant are results to the research query?
4. **Coverage**: Are there any gaps in the research?

Provide a quality score (1-10) and detailed explanation.
"""