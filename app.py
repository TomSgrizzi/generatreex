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
            \documentclass{letter}
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
    \documentclass{letter}
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

    ################  ISOLATING EACH CASES #######################

    def extract_words(sentence):
        words = []
        current_word = ''

        inside_brackets = False
        for char in sentence:
            if char == '[':
                inside_brackets = True
                if current_word:
                    words.append(current_word)
                    current_word = ''
            elif char == ']':
                inside_brackets = False
                if current_word:
                    words.append(current_word)
                    current_word = ''
            elif char == ' ' and not inside_brackets:
                if current_word:
                    words.append(current_word)
                    current_word = ''
            else:
                current_word += char

        if current_word:
            words.append(current_word)

        return words

    # Example usage:

    content_with_multiple_names = extract_words(corrected_string)
    print(content_with_multiple_names)
    # List: ["T',name=T' ", 'il,name=il Giulio,name=Giulio ', 'mangia,name=mangia ', 'la,name=la mela,name=mela bruna,name=bruna']


    ######## TENIAMO SOLO GLI ELEMENTI CHE SONO PROBLEMATICI #########

    def filter_elements_with_multiple_names(lst):
        """
        Filters elements in the list that contain the word 'name' more than once.
        
        Parameters:
        lst (list): The list to filter.

        Returns:
        list: A list containing only elements with 'name' occurring more than once.
        """
        filtered_list = []
        for item in lst:
            if item.count("name") > 1:
                filtered_list.append(item)
        return filtered_list

    # Example usage:
    filtered_result = filter_elements_with_multiple_names(content_with_multiple_names)
    print(str(filtered_result) + " filtered result checkpoint")
    # ['il,name=il Giulio,name=Giulio ', 'la,name=la mela,name=mela bruna,name=bruna']


    ######## HANDLING OF SPACES ################
    if filtered_result:
        def store_words_before_comma(input_string):
            words = ""
            word_list = []
            for char in input_string:
                if char == ',':
                    if words:  # Add the accumulated words before the comma to the list
                        word_list.append(words.strip())
                    words = ""
                else:
                    words += char
            if words:  # Append the last word if there's no comma at the end
                word_list.append(words.strip())

            # Reconstruct the sentence from the filtered words
            result = ' '.join(word_list)

            equal_words = result.split()

            filtered_words = [word for word in equal_words if "=" not in word]

            output = ' '.join(filtered_words)
            return output

        def substitute_word(text, old_word, new_word):
            return text.replace(old_word, new_word)

        print(""" 
                The benchmark is  """ + str(filtered_result))

        for i in filtered_result:

            corrected_label = store_words_before_comma(i)
            print(corrected_label + " was: " + i)

            new_label = corrected_label+",name="+corrected_label
            print("""
                    new label is """ + new_label)
            new_output = substitute_word(corrected_string, i, new_label)
            corrected_string = new_output
            print("Now the string is " + new_output)

        corrected_string = new_output

    print("The pairs of nodes are: ", node_pairs)
    #####cut here#####
    def count_brackets_between_words(tree_string, start_substring, end_substring):
        start_index = tree_string.find("["+start_substring)
        end_index = tree_string.find("["+end_substring)
        
        # Ensure that both substrings are found and start_substring comes before end_substring
        if start_index == -1 or end_index == -1 or start_index >= end_index:
            start_index = tree_string.find(end_substring)
            end_index = tree_string.find(start_substring)
            # Extract the section of the string between the two substrings
            section = tree_string[start_index:end_index]
        
            # Count the number of "]" in the section
            count = section.count(']')
        
            return count
        
        # Extract the section of the string between the two substrings
        section = tree_string[start_index:end_index]
        
        # Count the number of "]" in the section
        count = section.count(']')
        
        return count

    benchmark_for_extra_nodes = {}

    for pair in node_pairs:
        word1 = [pair.split(',')[0].strip()]
        word2 = [pair.split(',')[1].strip()]
        cleaned_word1 = word1[0].replace("['", "").replace("']", "")
        cleaned_word2 = word2[0].replace("['", "").replace("']", "")
        print(cleaned_word1)
        print(cleaned_word2)
        bracket_count = count_brackets_between_words(corrected_string, cleaned_word1, cleaned_word2)
        benchmark_for_extra_nodes[pair]=bracket_count
        print("Number of ']' characters between '['{}' and '['{}' is: {}".format(cleaned_word1, cleaned_word2, bracket_count))

    print(benchmark_for_extra_nodes)

    eccedenze_dictionary = {}
    normal_lines_dictionary = {}
    for key, value in benchmark_for_extra_nodes.items():
        if value > 3:
            eccedenze_dictionary[key]=value
        else:
            normal_lines_dictionary[key]=value

    print(eccedenze_dictionary)
    print(normal_lines_dictionary)

    tikz_string_template = f"\draw[->,dotted] ({source}) to[out=south west,in=south west] ({goal});"
    tikz_code = []

    scope_tikz_1 = r"\begin{scope}[every node/.style={circle}] \path"
    scope_tikz_2 = r"({source}) coordinate"
    scope_tikz_3 = r"({coordinate_in_the_tree}); \node" 
    scope_tikz_4 = r"[label=above:{}]"
    scope_tikz_5 = r" at ({source})"
    scope_tikz_6 = r"{}; \end{scope}"

    coordinate_tikz = r"\coordinate ({coordinatetopivot}) at ([xshift={xcoord}cm,yshift={ycoord}cm]{coordinata_in_the_tree});"

    extra_tikz = r"\draw[->,dotted] ({source}) to[out=south,in=east]({coordinatetopivot}) to[out=west,in=west]({goal});"

    print(eccedenze_dictionary)
    def assembling_modulating_formula(dic):
        for key, value in eccedenze_dictionary.items():
            print(value)
            xcoord = -(float(value)/2)
            ycoord = -(float(value)/2)
            print(xcoord)
            print(ycoord)
            nodes = key.split(',')
            source = nodes[0].strip()
            goal = nodes[1].strip()
            coord_name = "extra"+source
            coordinate_to_pivot = "pivot"+source
            specific_scope_2 = scope_tikz_2.format(source=source)
            specific_scope_tikz_3 = scope_tikz_3.format(coordinate_in_the_tree=coord_name,source=source)
            specific_scope_tikz_5 =scope_tikz_5.format(source=source)
            total_tikz_scope = scope_tikz_1 + specific_scope_2 + specific_scope_tikz_3 + scope_tikz_4 +specific_scope_tikz_5 +scope_tikz_6
            coordinates = coordinate_tikz.format(coordinatetopivot=coordinate_to_pivot, xcoord=xcoord,ycoord=ycoord,coordinata_in_the_tree=coord_name)
            print(coordinates)
            tikz_string = extra_tikz.format(source=source,coordinatetopivot=coordinate_to_pivot,goal=goal)
            print("The first extended tikz line computed is: "+total_tikz_scope + coordinates +tikz_string)
            tikz_code.append(total_tikz_scope + coordinates +tikz_string)


        print(tikz_code)

    #Let's store the tikz codes:
    normal_lines_tikz = ""
    extended_lines_tikz = ""

    if normal_lines_dictionary:
        for key, value in normal_lines_dictionary.items():
            nodes = key.split(',')
            print(nodes)
            if len(nodes) == 2:
                source = nodes[0].strip()
                print(source)
                goal = nodes[1].strip()
                print(goal)
                tikz_code_normal_lines = tikz_string_template.format(source=source, goal=goal)
                print(tikz_code_normal_lines)
                normal_lines_tikz += tikz_code_normal_lines
                print(normal_lines_tikz)
            else:
                print("Invalid pair: ", pair)

    if eccedenze_dictionary:
        assembling_modulating_formula(eccedenze_dictionary)

        for code in tikz_code:
            extended_lines_tikz += code

    print("The extended tikz lines are: "+extended_lines_tikz)

    print("The tikz code is: " + str(tikz_code_normal_lines))
    latex_document = latex_template.replace("{user_input}", corrected_string)
    latex_document = latex_document.replace("{movement_strings}", normal_lines_tikz+extended_lines_tikz)

    #####cut here#####

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

        session.pop('node_pairs', None) 
        # Return the URL for the download page
        return jsonify({"message": "The PDF file has been created", "url": url_for('download_page')})
    else:
        # Clear the user_input from the session
        session.pop('user_input', None)

        session.pop('node_pairs', None) 
        # Redirect to the main page
        return redirect(url_for('main'))

if __name__ == "__main__":
    app.run(debug=True)
