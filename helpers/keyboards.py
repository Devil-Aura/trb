from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_track_selection_keyboard(tracks, selected_indices, page=0, is_audio=True):
    # tracks: list of dicts {index, label, lang...}
    # selected_indices: set of indices currently selected to REMOVE (or keep? Logic says "Select The Track Which You Want to Remove")
    # Actually, logic says "Select The Track Which You Want to Remove". 
    # But usually "Green" implies selected. 
    # Let's assume Green = Selected for Removal? Or Green = Selected to Keep?
    # User said: "Select The Track Which You Want to Remove... If Audio Language Button Is Clicked Then It Turns to Green ... and also the selected track will removed."
    # So Green = Removed.
    
    ITEMS_PER_PAGE = 5
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_tracks = tracks[start:end]
    
    buttons = []
    
    for track in current_tracks:
        idx = track['index']
        label = track['label']
        
        # If selected (to remove), show Green/Check
        if idx in selected_indices:
            text = f"✅ {label}"
        else:
            text = label
            
        callback_data = f"toggle_{idx}_{page}_{'audio' if is_audio else 'sub'}"
        buttons.append([InlineKeyboardButton(text, callback_data=callback_data)])
        
    # Navigation
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⏮ Previous", callback_data=f"page_{page-1}_{'audio' if is_audio else 'sub'}"))
    
    if end < len(tracks):
        nav_buttons.append(InlineKeyboardButton("⏭ Next", callback_data=f"page_{page+1}_{'audio' if is_audio else 'sub'}"))
        
    if nav_buttons:
        buttons.append(nav_buttons)
        
    # Switch Mode / Done
    control_buttons = []
    if is_audio:
        control_buttons.append(InlineKeyboardButton("📄 Go to Subtitles", callback_data="switch_to_subs"))
    else:
        control_buttons.append(InlineKeyboardButton("📄 Go to Audio", callback_data="switch_to_audio"))
        
    control_buttons.append(InlineKeyboardButton("✅ Done", callback_data="process_done"))
    
    buttons.append(control_buttons)
    
    return InlineKeyboardMarkup(buttons)
