from agents import writer_runnable , build_reader_agent , critic_runnable , build_search_agent


def run_research_pipeline(topic :str) -> dict:
    state= {}


    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        'messages' : [("user" , f"Find recent , reliable detailed info about:{topic}")]
    })
    state["search_results"] = search_result['messages'][-1].content 

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages":[("user" ,
             f"based on the following search results about '{topic}',"
             f"pick most relevant url and scrape it for deeper content. \n\n" 
             f"search Results: \n{state['search_results'][:800]}"       
                     
        )]
    })

    state["scrape_content"] = reader_result['messages'][-1].content
    print("scrape content: " , state['scrape_content'])


    research_combined = (
        f"search results:  {state['search_results']}\n\n"
        f"detailed scraped content : \n{state['scrape_content']}"
    )

    state['report'] = writer_runnable.invoke({
        "topic": topic , 
        "research": research_combined
    })

    print("\n final Report" , state['report'])

    state["feedback"] = critic_runnable.invoke({
        "report" : state["report"]
    })

    print( "\ncritic report :", state['feedback'])

    return state


if __name__ == "__main__":
    topic = input("\n Enter a research topic:"  )
    run_research_pipeline(topic) 




