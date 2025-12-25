# Improvement: Notes Rich Text Rendering

**Category**: Improvements
**Task ID**: IMP-1
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

The Notes app currently saves rich text content (headings, bullet points, bold/italic) but does not properly render these elements when displaying notes. The content is stored correctly in the database, but the QML TextArea or Text components display it as plain text without formatting.

This improvement focuses on implementing proper rich text rendering so that:
- Headings (H1, H2) display with appropriate font sizes and weights
- Bullet points render as actual list items with proper indentation
- Bold and italic text display with correct styling
- The note preview in the list view shows a formatted snippet

### Current Behavior
- User types markdown-style or rich text formatting
- Content saves to database correctly
- When viewing the note, formatting appears as raw text (e.g., "# Heading" instead of styled heading)

### Expected Behavior
- Saved formatting renders visually in both the note editor and note list preview
- Seamless transition between editing and viewing modes
- Consistent rendering across all note views

## Technical Approaches

### Option A: Markdown Rendering
Convert stored markdown to HTML/rich text for display:
- Parse markdown syntax (# headings, - bullets, **bold**, *italic*)
- Convert to Qt Rich Text format
- Use TextEdit with `textFormat: TextEdit.RichText`

### Option B: HTML Storage
Store content as HTML and render directly:
- TextArea outputs HTML when editing
- Store HTML in database
- Render HTML in read mode using Text with `textFormat: Text.RichText`

### Option C: Custom Renderer
Build a custom QML component that parses and renders formatted text:
- More control over styling
- Better integration with Theme.qml
- More complex implementation

## Acceptance Criteria

- [ ] Headings (H1, H2) render with correct font size and weight
- [ ] Bullet points display as proper list items with bullets/indentation
- [ ] Bold text renders in bold
- [ ] Italic text renders in italics
- [ ] Note list preview shows formatted snippet (first few lines)
- [ ] Editing experience remains smooth and intuitive
- [ ] Format persists correctly when saving and reopening notes
- [ ] Performance acceptable for notes with significant formatting

## Files to Modify

- `device/apps/ui/qml/NoteEditor.qml` - Add rich text rendering
- `device/apps/ui/qml/NotesList.qml` - Format preview text
- `device/apps/ui/qml/components/` - Add RichTextRenderer component (if needed)

## Tests Required

- [ ] Manual verification: Create note with H1, H2 headings
- [ ] Manual verification: Create note with bullet points
- [ ] Manual verification: Create note with bold/italic
- [ ] Manual verification: Reopen note and verify formatting persists
- [ ] Manual verification: Note preview shows formatted text

## Implementation Notes

{Add notes during implementation}

## Validation Commands

```bash
# Run the UI application
cd device/apps/ui && python main.py

# Navigate to Notes app
# Create a new note with various formatting
# Save and reopen to verify rendering
```

## Completion Checklist

- [ ] Code implemented
- [ ] Tests written
- [ ] Tests passing
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Files committed

## Time Tracking

- Estimated effort: 3-4 hours
- Actual effort: {to be filled}

## Blockers

None

## Related Tasks

- Related to: 12.6 Notes App (COMPLETED)
- May relate to: Future rich text needs in other apps (AI chat, Mesh messages)
