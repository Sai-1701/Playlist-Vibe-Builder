# Import time so Auto Play can pause between updates
import time

# Import Gradio for the web-based interface
import gradio as gr


# Example playlist data for quick testing
# Each line follows the format:
# title,artist,energy,duration
SAMPLE_PLAYLIST = """Blinding Lights,The Weeknd,85,200
Starboy,The Weeknd,90,230
Peaches,Justin Bieber,65,198
Sorry,Justin Bieber,70,205
Sweater Weather,The Neighbourhood,75,240
Daddy Issues,The Neighbourhood,60,230
Hush,The Marías,40,210
Cariño,The Marías,55,195"""


# Convert the textbox input into a playlist the program can sort
# This function also checks that every song is entered correctly
def parse_playlist(text):
    # Remove extra spaces around the full input
    text = text.strip()

    # Return an empty list if the input box is blank
    if text == "":
        return []

    # Split the input so each line becomes one song entry
    lines = text.split("\n")

    # Store validated songs here
    playlist = []

    # Process each line one at a time
    for line_number in range(len(lines)):
        # Remove extra spaces from the current line
        line = lines[line_number].strip()

        # Ignore completely blank lines
        if line == "":
            continue

        # Split the line into its 4 expected values
        parts = line.split(",")

        # A valid song must have exactly 4 pieces of information
        if len(parts) != 4:
            raise ValueError(
                f"Line {line_number + 1} must be: title,artist,energy,duration"
            )

        # Read each value and remove extra spaces
        title = parts[0].strip()
        artist = parts[1].strip()
        energy_text = parts[2].strip()
        duration_text = parts[3].strip()

        # Titles are required because they identify each bar and playlist item
        if title == "":
            raise ValueError(f"Line {line_number + 1}: title cannot be empty")

        # Artist names are also required for complete playlist data
        if artist == "":
            raise ValueError(f"Line {line_number + 1}: artist cannot be empty")

        # Convert energy to an integer so it can be compared numerically
        try:
            energy = int(energy_text)
        except ValueError:
            raise ValueError(f"Line {line_number + 1}: energy must be a whole number")

        # Energy must stay in the project range of 0 to 100
        if energy < 0 or energy > 100:
            raise ValueError(f"Line {line_number + 1}: energy must be between 0 and 100")

        # Convert duration to an integer so it can also be sorted numerically
        try:
            duration = int(duration_text)
        except ValueError:
            raise ValueError(f"Line {line_number + 1}: duration must be a whole number")

        # A song length must be positive
        if duration <= 0:
            raise ValueError(f"Line {line_number + 1}: duration must be greater than 0")

        # Store each valid song as a dictionary for easy access by key name
        playlist.append(
            {
                "title": title,
                "artist": artist,
                "energy": energy,
                "duration": duration
            }
        )

    # Return the finished playlist after all validation is complete
    return playlist


# Turn the sorted playlist into readable text for the output box
def format_playlist_text(playlist):
    # Show a simple message if there is nothing to display
    if len(playlist) == 0:
        return "Playlist is empty."

    # Build one line per song
    output = []

    # Add every song in its current order
    for i in range(len(playlist)):
        song = playlist[i]
        output.append(
            f"{i + 1}. {song['title']} | {song['artist']} | "
            f"Energy: {song['energy']} | Duration: {song['duration']} sec"
        )

    # Join the lines into one block of text
    return "\n".join(output)


# Build the visualization for one saved sorting step
# The bars represent either energy or duration depending on the chosen key
def build_step_html(playlist, key, highlight_indices=None, placed_indices=None):
    # Use empty lists if no special bars were provided
    if highlight_indices is None:
        highlight_indices = []

    if placed_indices is None:
        placed_indices = []

    # Show a styled message if there is no playlist to visualize
    if len(playlist) == 0:
        return """
        <div style="
            padding:24px;
            font-family:Arial, sans-serif;
            color:#5f4b73;
            background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
            border-radius:20px;
            border:1px solid #e6dff2;
            text-align:center;
            box-shadow:0 4px 14px rgba(170,150,200,0.15);
        ">
            No playlist to display.
        </div>
        """

    # Find the largest selected value so every bar can be scaled proportionally
    max_value = 1
    for song in playlist:
        if song[key] > max_value:
            max_value = song[key]

    # Start the main chart container
    html = """
    <div style="
        font-family:Arial, sans-serif;
        padding:18px;
        background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
        border-radius:22px;
        border:1px solid #e6dff2;
        box-shadow:0 6px 18px rgba(170,150,200,0.18);
    ">
      <div style="
          margin-bottom:12px;
          font-size:16px;
          font-weight:700;
          color:#6c5586;
          text-align:center;
      ">
        Playlist Visualization
      </div>
      <div style="
          margin-bottom:14px;
          font-size:13px;
          color:#5f4b73;
          display:flex;
          gap:18px;
          flex-wrap:wrap;
          justify-content:center;
          align-items:center;
      ">
        <span>
          <span style="
              display:inline-block;
              width:14px;
              height:14px;
              background:#cdb4ff;
              border:1px solid #8f7aaa;
              border-radius:4px;
              margin-right:6px;
              vertical-align:middle;
          "></span>
          Normal
        </span>
        <span>
          <span style="
              display:inline-block;
              width:14px;
              height:14px;
              background:#ffb3c7;
              border:1px solid #8f7aaa;
              border-radius:4px;
              margin-right:6px;
              vertical-align:middle;
          "></span>
          Comparing
        </span>
        <span>
          <span style="
              display:inline-block;
              width:14px;
              height:14px;
              background:#c7ead3;
              border:1px solid #8f7aaa;
              border-radius:4px;
              margin-right:6px;
              vertical-align:middle;
          "></span>
          Placed
        </span>
      </div>
      <div style="
          display:flex;
          align-items:flex-end;
          gap:12px;
          height:340px;
          padding:18px;
          border:1px solid #e8e1f3;
          border-radius:18px;
          background:rgba(255,255,255,0.88);
          overflow-x:auto;
      ">
    """

    # Add one bar for every song in the current step
    for i in range(len(playlist)):
        # Read the current song and chosen value
        song = playlist[i]
        value = song[key]

        # Scale the bar height so it fits inside the same chart area
        height = int((value / max_value) * 220) + 24

        # Use a default color for bars not currently being emphasized
        color = "#cdb4ff"

        # Highlight grouped comparison/placement steps clearly
        if i in highlight_indices:
            color = "#ffb3c7"

        # Highlight newly placed values to show how the merged result is being built
        if i in placed_indices:
            color = "#c7ead3"

        # Shorten long titles so labels stay readable
        short_title = song["title"]
        if len(short_title) > 10:
            short_title = short_title[:10] + "..."

        # Add the bar and its labels to the chart
        html += f"""
        <div style="
            display:flex;
            flex-direction:column;
            align-items:center;
            min-width:92px;
        ">
          <div style="
              font-size:12px;
              margin-bottom:8px;
              color:#5f4b73;
              font-weight:600;
          ">
              {value}
          </div>
          <div style="
              width:72px;
              height:{height}px;
              background:{color};
              border:1px solid #8f7aaa;
              border-radius:16px 16px 6px 6px;
              box-shadow:0 4px 10px rgba(150,130,180,0.20);
          "></div>
          <div style="
              font-size:11px;
              margin-top:8px;
              text-align:center;
              color:#5f4b73;
              line-height:1.2;
              max-width:80px;
          ">
              {short_title}
          </div>
        </div>
        """

    # Close the chart container
    html += """
      </div>
    </div>
    """

    # Return the finished HTML for this step
    return html


# Save one moment of the sorting process
# A copy of the playlist is stored so earlier steps do not get overwritten later
def add_step(steps, playlist, key, message, highlight_indices=None, placed_indices=None):
    steps.append(
        {
            "playlist": [song.copy() for song in playlist],
            "message": message,
            "html": build_step_html(playlist, key, highlight_indices, placed_indices)
        }
    )


# Merge two already sorted halves back into one sorted section
# This is the core action that makes Merge Sort work
def merge(data, left, mid, right, key, steps):
    # Temporary lists protect the left and right halves while values are being compared
    left_part = []
    right_part = []

    # Copy the left half into its own temporary list
    i = left
    while i <= mid:
        left_part.append(data[i].copy())
        i += 1

    # Copy the right half into its own temporary list
    j = mid + 1
    while j <= right:
        right_part.append(data[j].copy())
        j += 1

    # These pointers track the current position in each temporary half
    left_index = 0
    right_index = 0

    # This pointer marks where the next smallest item should go in the main list
    merged_index = left

    # Keep comparing until one temporary list runs out of values
    while left_index < len(left_part) and right_index < len(right_part):
        # Decide which value should be placed next in the merged section
        # Using <= keeps equal values in their original order, which makes Merge Sort stable
        if left_part[left_index][key] <= right_part[right_index][key]:
            data[merged_index] = left_part[left_index].copy()

            # Save one grouped step instead of separate compare and place steps
            add_step(
                steps,
                data,
                key,
                f"Compared {left_part[left_index]['title']} ({left_part[left_index][key]}) with {right_part[right_index]['title']} ({right_part[right_index][key]}), then placed {left_part[left_index]['title']} into position {merged_index + 1}",
                highlight_indices=[merged_index],
                placed_indices=[merged_index]
            )

            left_index += 1
        else:
            data[merged_index] = right_part[right_index].copy()

            # Save one grouped step instead of separate compare and place steps
            add_step(
                steps,
                data,
                key,
                f"Compared {left_part[left_index]['title']} ({left_part[left_index][key]}) with {right_part[right_index]['title']} ({right_part[right_index][key]}), then placed {right_part[right_index]['title']} into position {merged_index + 1}",
                highlight_indices=[merged_index],
                placed_indices=[merged_index]
            )

            right_index += 1

        # Move to the next open position in the merged section
        merged_index += 1

    # If the left half still has values, they are already in sorted order and can be copied directly
    while left_index < len(left_part):
        data[merged_index] = left_part[left_index].copy()

        add_step(
            steps,
            data,
            key,
            f"Added remaining {left_part[left_index]['title']} into position {merged_index + 1}",
            placed_indices=[merged_index]
        )

        left_index += 1
        merged_index += 1

    # If the right half still has values, copy them as well
    while right_index < len(right_part):
        data[merged_index] = right_part[right_index].copy()

        add_step(
            steps,
            data,
            key,
            f"Added remaining {right_part[right_index]['title']} into position {merged_index + 1}",
            placed_indices=[merged_index]
        )

        right_index += 1
        merged_index += 1


# Recursively split the playlist into smaller sections, then merge them back in sorted order
# This divide-and-conquer structure is what gives Merge Sort its efficiency
def merge_sort(data, left, right, key, steps):
    # A section with one or zero items is already sorted
    # This is the base case that stops the recursion
    if left >= right:
        return

    # Find the midpoint so the section can be divided into two halves
    mid = (left + right) // 2

    # Save the split step so the user can follow how the list is being divided
    add_step(
        steps,
        data,
        key,
        f"Splitting section from position {left + 1} to position {right + 1}"
    )

    # Sort the left half
    merge_sort(data, left, mid, key, steps)

    # Sort the right half
    merge_sort(data, mid + 1, right, key, steps)

    # Save the merge step so the user sees when two sorted halves are being combined
    add_step(
        steps,
        data,
        key,
        f"Merging section from position {left + 1} to position {right + 1}"
    )

    # Merge the two sorted halves together
    merge(data, left, mid, right, key, steps)


# Prepare every sorting step before the user starts stepping through them
# This function validates input, runs Merge Sort, and builds the final sorted output
def prepare_sort(playlist_text, sort_key):
    try:
        # Convert the user's raw textbox input into playlist data
        playlist = parse_playlist(playlist_text)

        # Stop early if the playlist is empty
        if len(playlist) == 0:
            empty_html = """
            <div style="
                padding:24px;
                font-family:Arial, sans-serif;
                color:#5f4b73;
                background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
                border-radius:20px;
                border:1px solid #e6dff2;
                text-align:center;
                box-shadow:0 4px 14px rgba(170,150,200,0.15);
            ">
                No playlist to display.
            </div>
            """
            return [], 0, empty_html, "Please enter at least one song.", "No sorted playlist yet.", "Step 0 of 0"

        # Store every visual step here
        steps = []

        # Save the unsorted starting state
        add_step(
            steps,
            playlist,
            sort_key,
            f"Starting Merge Sort by {sort_key}"
        )

        # Work on a copy so the original parsed playlist does not get overwritten unexpectedly
        working_playlist = [song.copy() for song in playlist]

        # Run the manual Merge Sort algorithm
        merge_sort(working_playlist, 0, len(working_playlist) - 1, sort_key, steps)

        # Mark every index as placed for the final visual
        final_sorted_indices = []
        i = 0
        while i < len(working_playlist):
            final_sorted_indices.append(i)
            i += 1

        # Save one final completed step
        steps.append(
            {
                "playlist": [song.copy() for song in working_playlist],
                "message": "Sorting complete.",
                "html": build_step_html(working_playlist, sort_key, placed_indices=final_sorted_indices)
            }
        )

        # Build the readable final sorted playlist text
        final_text = format_playlist_text(working_playlist)

        # Return the prepared steps and the first display state
        return steps, 0, steps[0]["html"], steps[0]["message"], final_text, f"Step 1 of {len(steps)}"

    # Return a clean error message instead of letting the app crash on bad input
    except Exception as e:
        error_html = """
        <div style="
            padding:24px;
            font-family:Arial, sans-serif;
            color:#6f4c69;
            background:linear-gradient(180deg, #fff4f8, #fff9fc);
            border-radius:20px;
            border:1px solid #f0d9e6;
            text-align:center;
            box-shadow:0 4px 14px rgba(210,170,190,0.15);
        ">
            Input error.
        </div>
        """
        return [], 0, error_html, f"Input Error: {str(e)}", "No sorted playlist yet.", "Step 0 of 0"


# Display one previously saved step
# This lets the user move through the algorithm like a slideshow
def show_step(steps, step_index):
    # If no steps exist, return a default message
    if not steps:
        return (
            """
            <div style="
                padding:24px;
                font-family:Arial, sans-serif;
                color:#5f4b73;
                background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
                border-radius:20px;
                border:1px solid #e6dff2;
                text-align:center;
                box-shadow:0 4px 14px rgba(170,150,200,0.15);
            ">
                No steps to show.
            </div>
            """,
            "No steps prepared.",
            "Step 0 of 0"
        )

    # Prevent the step index from going below the first step
    if step_index < 0:
        step_index = 0

    # Prevent the step index from going past the last step
    if step_index >= len(steps):
        step_index = len(steps) - 1

    # Read the selected step
    step = steps[step_index]

    # Return the stored visual, message, and progress label
    return step["html"], step["message"], f"Step {step_index + 1} of {len(steps)}"


# Move one step forward through the saved sorting process
def next_step(steps, step_index):
    # If there are no steps, keep the app in an empty state
    if not steps:
        return (
            step_index,
            """
            <div style="
                padding:24px;
                font-family:Arial, sans-serif;
                color:#5f4b73;
                background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
                border-radius:20px;
                border:1px solid #e6dff2;
                text-align:center;
                box-shadow:0 4px 14px rgba(170,150,200,0.15);
            ">
                No steps to show.
            </div>
            """,
            "No steps prepared.",
            "Step 0 of 0"
        )

    # Move forward by one step
    step_index += 1

    # Stop at the final step instead of going out of range
    if step_index >= len(steps):
        step_index = len(steps) - 1

    # Show the new step
    html, message, counter = show_step(steps, step_index)

    return step_index, html, message, counter


# Move one step backward through the saved sorting process
def previous_step(steps, step_index):
    # If there are no steps, keep the app in an empty state
    if not steps:
        return (
            step_index,
            """
            <div style="
                padding:24px;
                font-family:Arial, sans-serif;
                color:#5f4b73;
                background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
                border-radius:20px;
                border:1px solid #e6dff2;
                text-align:center;
                box-shadow:0 4px 14px rgba(170,150,200,0.15);
            ">
                No steps to show.
            </div>
            """,
            "No steps prepared.",
            "Step 0 of 0"
        )

    # Move backward by one step
    step_index -= 1

    # Stop at the first step instead of going below zero
    if step_index < 0:
        step_index = 0

    # Show the new step
    html, message, counter = show_step(steps, step_index)

    return step_index, html, message, counter


# Play every saved step automatically with a small pause between them
# This makes the sorting process feel animated instead of fully manual
def auto_play(steps):
    # If no steps exist, return an empty display once
    if not steps:
        yield (
            0,
            """
            <div style="
                padding:24px;
                font-family:Arial, sans-serif;
                color:#5f4b73;
                background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
                border-radius:20px;
                border:1px solid #e6dff2;
                text-align:center;
                box-shadow:0 4px 14px rgba(170,150,200,0.15);
            ">
                No steps to show.
            </div>
            """,
            "No steps prepared.",
            "Step 0 of 0"
        )
        return

    # Stream each step one by one to the interface
    for step_index in range(len(steps)):
        step = steps[step_index]

        yield (
            step_index,
            step["html"],
            step["message"],
            f"Step {step_index + 1} of {len(steps)}"
        )

        # Pause so the user has time to see each grouped step
        time.sleep(0.8)


# Load the example playlist into the textbox
def load_sample():
    return SAMPLE_PLAYLIST


# Reset the app back to its starting state
def clear_all():
    empty_html = """
    <div style="
        padding:24px;
        font-family:Arial, sans-serif;
        color:#5f4b73;
        background:linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%);
        border-radius:20px;
        border:1px solid #e6dff2;
        text-align:center;
        box-shadow:0 4px 14px rgba(170,150,200,0.15);
    ">
        No playlist to display.
    </div>
    """

    return "", [], 0, empty_html, "Ready.", "Step 0 of 0", "No sorted playlist yet."


# Build the interface using a soft theme and a simple layout
with gr.Blocks(
    title="Playlist Vibe Builder",
    theme=gr.themes.Soft(
        primary_hue="purple",
        secondary_hue="pink",
        neutral_hue="slate"
    ),
    css="""
    body, .gradio-container {
        background: linear-gradient(180deg, #fff8fc 0%, #f4ecff 50%, #eef7ff 100%) !important;
    }
    .gradio-container {
        font-family: Arial, sans-serif;
    }
    .gr-button {
        border-radius: 16px !important;
    }
    .gr-textbox, .gr-radio {
        border-radius: 16px !important;
    }
    """
) as demo:
    # Main title
    gr.Markdown("## Playlist Vibe Builder")

    # Short instructions for the user
    gr.Markdown(
        "Enter one song per line in this format:\n"
        "`title,artist,energy,duration`\n\n"
        "Click **Prepare Merge Sort** to create the steps, then use **Previous Step**, **Next Step**, or **Auto Play** to follow the sorting."
    )

    # Store every prepared sorting step
    steps_state = gr.State([])

    # Store the current step index
    step_index_state = gr.State(0)

    # Place the playlist input and sorting choice side by side
    with gr.Row():
        # Text input for the playlist
        playlist_input = gr.Textbox(
            label="Playlist Input",
            lines=10,
            placeholder="Blinding Lights,The Weeknd,85,200\nStarboy,The Weeknd,90,230"
        )

        # Let the user choose the sorting key
        sort_key = gr.Radio(
            choices=["energy", "duration"],
            value="energy",
            label="Sort By"
        )

    # Group the main action buttons together
    with gr.Row():
        sample_button = gr.Button("Load Sample Playlist")
        prepare_button = gr.Button("Prepare Merge Sort", variant="primary")
        auto_button = gr.Button("Auto Play")
        clear_button = gr.Button("Clear")

    # Display the current bar chart step
    visualization = gr.HTML(label="Visualization")

    # Display the explanation of the current step
    current_message = gr.Textbox(label="Current Step", lines=3)

    # Show the step number
    step_counter = gr.Textbox(label="Progress", lines=1)

    # Buttons for manual navigation
    with gr.Row():
        previous_button = gr.Button("Previous Step")
        next_button = gr.Button("Next Step")

    # Textbox for the final sorted playlist
    final_sorted_output = gr.Textbox(label="Final Sorted Playlist", lines=10)

    # Fill the input box with example data
    sample_button.click(
        fn=load_sample,
        inputs=[],
        outputs=[playlist_input]
    )

    # Parse the input, run Merge Sort, and build every step
    prepare_button.click(
        fn=prepare_sort,
        inputs=[playlist_input, sort_key],
        outputs=[steps_state, step_index_state, visualization, current_message, final_sorted_output, step_counter]
    )

    # Move backward through the saved steps
    previous_button.click(
        fn=previous_step,
        inputs=[steps_state, step_index_state],
        outputs=[step_index_state, visualization, current_message, step_counter]
    )

    # Move forward through the saved steps
    next_button.click(
        fn=next_step,
        inputs=[steps_state, step_index_state],
        outputs=[step_index_state, visualization, current_message, step_counter]
    )

    # Play the sorting process automatically
    auto_button.click(
        fn=auto_play,
        inputs=[steps_state],
        outputs=[step_index_state, visualization, current_message, step_counter]
    )

    # Reset everything
    clear_button.click(
        fn=clear_all,
        inputs=[],
        outputs=[
            playlist_input,
            steps_state,
            step_index_state,
            visualization,
            current_message,
            step_counter,
            final_sorted_output
        ]
    )

# Launch the app
demo.launch()