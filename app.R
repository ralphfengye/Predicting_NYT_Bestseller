library(ggplot2)
library(shiny)
library(plotly)
library(tools)

df = readRDS("data_shiny.rds")


ui <- fluidPage(
  titlePanel(title=h4("New York Times Bestseller List Interactive Graphs (Hardcover Fictions)")),
  sidebarPanel(
    
    #Built input box to enter title and author, along with submit and clear buttons
    textInput("inputBook", "Title", value="Enter Book Name"),
    textInput("inputAuthor", "Author", value="Enter Author Name"),
    actionButton("submit", "Submit"),
    actionButton("clear", "Clear")
    
  ),
  mainPanel(
    h5("Graphs may take up to a minute to load"),
    
    #Display graphs with info on ranking and number of weeks 
    plotlyOutput("graph_week"),
    plotlyOutput("graph_rank"),
    htmlOutput("text"),
    htmlOutput("text2")
  )
)

server <- function(input, output, session) {
  plot_data <- reactive({
    return (df)  
  })
  key <- reactiveValues(rank=0, week=0, input_agg="", 
  rank_act=0, week_act=0, rank_pred=0, week_pred=0)
  
  observeEvent(input$submit, {
    #Execute when submit button is clicked
    
    #Aggregate user input to be the equivalent of title_author field
    key$input_agg <- paste(toupper(trimws(input$inputBook)), 
    toTitleCase(tolower(trimws(input$inputAuthor))), sep = " by ")
    #Sort dateframe based on weeks(descending) and title_author
    temp_df <- df[order(-df$weeks_on_list, df$title_author),]
    #Extract row number of the sorted dataframe
    key$week <- which(temp_df$title_author==key$input_agg)
    #Extract actual and predicted values
    key$week_act <- temp_df[key$week, "weeks_on_list"]
    key$week_pred <- round(temp_df[key$week, "week_pred"], digits=2)
    temp_df <- df[order(df$rank, df$title_author),]
    key$rank <- which(temp_df$title_author==key$input_agg)
    key$rank_act <- round(temp_df[key$rank, "rank"], digits=2)
    key$rank_pred <- round(temp_df[key$rank, "rank_pred"], digits=2)
  })
  
  observeEvent(input$clear, {
    #Execute when clear button is clicked
    key$rank <- 0
    key$week <- 0
    key$rank_act <- 0
    key$week_act <- 0
    key$rank_pred <- 0
    key$week_pred <- 0
    
    #Clear text from input box
    updateTextInput(session, "inputBook", label="Title", value="")
    updateTextInput(session, "inputAuthor", label="Author", value="")
  })
  
  output$graph_week <- renderPlotly({
    
    #Wrap ggplot density graph with plotly
    p1 <- ggplot(aes(x=reorder(title_author, -weeks_on_list), y=weeks_on_list,
      text=paste("Title:", title, "<br>", "Author:", author, "<br>", 
      "Total Weeks:", weeks_on_list)), 
      data=plot_data()) + geom_density(alpha=0.2, col="#56B4E9") +
      #Insert a vertical line indicating the position on the graph of the book user enters
      geom_vline(aes(xintercept=key$week)) +
      theme(axis.ticks.x=element_blank(), axis.text.x=element_blank(), 
      axis.title.x=element_blank())
    ggplotly(p1, tooltip=c("text"))
  })
  
  output$graph_rank <- renderPlotly({

    p2 <- ggplot(aes(x=reorder(title_author, rank), y=rank, 
      text=paste("Title:", title, "<br>", "Author:", 
      author, "<br>", "Average Rank:", rank)), data=plot_data()) + 
      geom_density(alpha=0.2, col="#009E73") +
      geom_vline(aes(xintercept=key$rank)) +
      theme(axis.ticks.x=element_blank(), 
      axis.text.x=element_blank(), axis.title.x=element_blank())
    ggplotly(p2, tooltip=c("text"))
  })
  
  output$text <- renderUI({
    str1 <- paste("Total Weeks:", key$week_act)
    str2 <- paste("Average Rank:", key$rank_act)
    HTML(paste(str1, str2, sep='\t'))
  })
  
  output$text2 <- renderUI({
    str1 <- paste("Predicted Weeks:", key$week_pred)
    str2 <- paste("Predicted Rank:", key$rank_pred)
    HTML(paste(str1, str2, sep='\t'))
  })
}

shinyApp(ui=ui, server=server)