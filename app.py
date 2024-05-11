from flask import Flask, request, render_template, session, redirect, url_for, flash, send_file, jsonify
import matplotlib.pyplot as plt
import os
import subprocess
import re

app = Flask(__name__)
# You need to set a secret key to use sessions
app.secret_key = os.environ.get('SECRET_KEY', 'default_key')
app.config['DEBUG'] = False
@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        # Retrieve data from textarea
        user_input = request.form.get('structure-input')
        
        def starts_with_bracket(string):
            return string.startswith("[")

        if not user_input.startswith("["):
            flash("Your structure must begin with an opening square bracket!")
            return redirect(url_for('main')) 

        if "[" not in user_input:
            return render_template('index.html')

        # Count the occurrences of '[' and ']'
        count_open_brackets = user_input.count('[')
        count_close_brackets = user_input.count(']')

        # Check if the counts are equal
        if count_open_brackets != count_close_brackets:
            flash('Invalid bracketing in the input. Check your structure.', 'error')
            return render_template('index.html')

        # Store the user input in the session
        session['user_input'] = user_input
        print("User input stored in session:", session['user_input'])  # Debug print
        # Redirect to the confirmation page
        return redirect(url_for('confirm'))
    return render_template('index.html')

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    if request.method == 'POST':
        #Retrieve the user input
        user_input = session.get('user_input', '')
        print("User input retrieved from session:", user_input)  # Debug print
        # Retrieve the user confirmation (yes or no)
        user_confirmation = request.form.get('confirmation')
        print("User confirmation:", user_confirmation)  # Debug print
        # Store the confirmation in the session
        session['confirmation'] = user_confirmation
        
        # Now you can use the confirmation in a conditional statement
        if user_confirmation == 'yes':
            # Do something if user confirms 'yes'
            return redirect(url_for('movement'))
        elif user_confirmation == 'no':
            # Do something if user confirms 'no'
            # Step 1: Write the LaTeX Template
            latex_template = r'''
            \documentclass{standalone}
            \usepackage{tikz}
            \usepackage{forest}

            \begin{document}
            \begin{forest}
                for tree={calign=fixed edge angles},
                {user_input}
            \end{forest}
            \end{document}
            '''


            # Replace placeholder with user's input
            latex_document = latex_template.replace("{user_input}", user_input)
            print("Latex document:", latex_document)  # Debug print


            # Write the LaTeX code to a file
            with open("document.tex", "w") as file:
                file.write(latex_document)

            subprocess.run(["pdflatex", "document.tex"])

            if os.path.exists("document.pdf"):
                # Convert PDF to PNG using pdftoppm
                subprocess.run(["pdftoppm", "-png", "-rx", "300", "-ry", "300", "document.pdf", "output"])
                print("The PNG file has been created.")
            else:
                print("PDF generation failed.")


        # Redirect to the next page or back to main, depending on your app logic
        return redirect(url_for('download_page'))  

    # Retrieve the user input from the session
    user_input = session.get('user_input', '')
    if not user_input:
        # If there's no user input in session, redirect to main to get input
        return redirect(url_for('main'))

    # Render the confirmation template, passing the user input
    return render_template('index2.html', user_input=user_input)

# Correct the endpoint name for the download route
@app.route('/download')
def download_page():
    return render_template('download.html')

# Correct the endpoint name for the file download route
@app.route('/download-pdf')
def download_pdf():
    try:
        return send_file('document.pdf', as_attachment=True)
    except FileNotFoundError:
        flash('File not found.', 'error')
        return redirect(url_for('download_page'))
    
@app.route('/movement')
def movement():
    return render_template('movements.html')
    
@app.route('/handle_proceed', methods=['POST'])
def handle_proceed():
    user_input = session.get('user_input', '')
    print('The tree structure is: ' + user_input)
    node_pairs = request.json.get('nodePairs', [])

    if node_pairs is None:
        # Return a response asking the user to input the node pairs again
        return jsonify({"error": "Node pairs are missing, please input the pairs again."}), 400

    print("The pairs of nodes are: ", node_pairs)  # Make sure to print the list, not concatenate it

    def is_even_lenght(lst):
        return len(lst) % 2 == 0  # Return the result

    
    latex_template = r'''
    \documentclass{standalone}
    \usepackage{tikz}
    \usepackage{forest}

    \begin{document}
    \begin{forest}
        for tree={calign=fixed edge angles},
        {user_input}
        {movement_strings}
    \end{forest}
    \end{document}
    '''
    # Use a regular expression to match words that may end with an apostrophe
    pattern = re.compile(r"(\b\w+'?\b)")

    # Function to add ",name=element" to each element
    def add_name_attr(match):
        element = match.group(1)  # The matched element including an apostrophe if present
        return f"{element},name={element}"

    # Replace elements in user_input using the add_name_attr function
    output_tree = pattern.sub(add_name_attr, user_input)

    # Regular expression to match the patterns where the element after "=" is followed by an apostrophe
    pattern = re.compile(r"(\w+)(,name=\w+')" )

    # Function to add an apostrophe before the comma if the element after "=" is followed by an apostrophe
    def add_apostrophe_before_comma(match):
        return f"{match.group(1)}',name={match.group(2)[5:]}"

    # Replace the matched patterns in the string using the add_apostrophe_before_comma function
    modified_string = pattern.sub(add_apostrophe_before_comma, output_tree)
    corrected_string = re.sub(r"name=+", "name=", modified_string)
    print("The processed tree structure is: " + corrected_string)

    print("The pairs of nodes are: ", node_pairs)

    tikz_string_template = "\draw[->,dotted] ({source}) to[out=south west,in=south west] ({goal});"
    tikz_code = ""

    # Iterate over the list of node pairs
    for pair in node_pairs:
        # Split the pair into source and goal nodes
        nodes = pair.split(',')
        if len(nodes) == 2:
            source = nodes[0].strip()
            goal = nodes[1].strip()
            movement_string = tikz_string_template.format(source=source, goal=goal)
            tikz_code += movement_string
        else:
            print("Invalid pair: ", pair)

    print("The tikz code is: " + tikz_code)
    latex_document = latex_template.replace("{user_input}", corrected_string)
    latex_document = latex_document.replace("{movement_strings}", tikz_code)
    
    print("Latex document:", latex_document)  # Debug print

    # Write the LaTeX code to a file
    with open("document.tex", "w") as file:
        file.write(latex_document)

    try:
        # Run pdflatex with a timeout to avoid hanging
        result = subprocess.run(["pdflatex", "document.tex"], timeout=30, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # If the return code indicates an error, handle it
        if result.returncode != 0:
            print("pdflatex failed with return code:", result.returncode)
            print("Standard Output:", result.stdout.decode())
            print("Standard Error:", result.stderr.decode())
            raise subprocess.CalledProcessError(result.returncode, "pdflatex")
    except subprocess.CalledProcessError as e:
        print("An error occurred while generating the PDF:", e)
        return jsonify({"error": "PDF generation failed"}), 500
    except subprocess.TimeoutExpired as e:
        print("The pdflatex command timed out:", e)
        return jsonify({"error": "PDF generation timed out"}), 500



    # ... (rest of your Flask route code)

    if os.path.exists("document.pdf"):
        # Clear the user_input from the session
        session.pop('user_input', None)
        # Return the URL for the download page
        return jsonify({"message": "The PDF file has been created", "url": url_for('download_page')})
    else:
        # Clear the user_input from the session
        session.pop('user_input', None)
        # Redirect to the main page
        return redirect(url_for('main'))

if __name__ == "__main__":
    app.run(debug=True)