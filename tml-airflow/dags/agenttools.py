# Agent Tool
from langchain_core.tools import tool
from email.mime.text import MIMEText
from email.message import EmailMessage
import smtplib


"""
You must define all your tools here for your agents to execute
You can define as many agents tools you want

YOU MUST ALSO update funcname

funcname = ["web_search:search_agent:You are a search expert","add:math_expert:You are a math expert","maxagent:max_agent:You find the company with maximum employees"]

The format is funcname = ["<function name>,<function_name>:<agent name>:<prompt>","<function name>:<agent name>:<prompt>",...]

NOTE: You can assign multiple functions to agents - separate multiple functions by a comma
"""

# SendEmail by Agent
@tool
def send_email(smtp_server: str, smtp_port: int, username: str, password: str,
                    sender: str, recipient: str, subject: str, body: str) -> bool:
    """
    Sends an email reply via SMTP using the generated response.
    """

    recemails = recipient.split(",")
    
    try:        
        # Use the updated format_email which preserves body line breaks        
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = username
        msg["To"] = recipient
        msg.set_content(body)
        
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(username, password)
#            server.send_message(msg)
            server.sendmail(username, recemails, msg.as_string())
        
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False    

#send_email({"smtp_server":"smtp.gmail.com","smtp_port":587,"username":SMTP_USERNAME,"password":SMTP_PASSWORD,"sender":SMTP_USERNAME,"recipient":recipientlist,"subject":"test","body":"test 2"})

# Example: Add two numbers
@tool
def add(a: float, b: float) -> float:
    '''Add two numbers.'''
    return a + b


@tool
def web_search(query: str) -> str:
    '''Search the web for information.'''
    return "Searched the web"

@tool
def max_agent(query: list) -> int:
    '''Find the company with the most employees.'''
    print(query)
    return max(query)

