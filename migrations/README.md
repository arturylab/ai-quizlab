# Database Migrations 📁

This folder contains database migration files for AI QuizLab.

## Available Files

### `question_bank.csv`
Complete question bank export containing 350 pre-created questions.

**Format**: CSV with columns:
- `id`: Question ID (auto-generated)
- `question`: Question text
- `option_a`: First option
- `option_b`: Second option  
- `option_c`: Third option
- `option_d`: Fourth option
- `correct_answer`: Correct option (A, B, C, or D)
- `category`: Subject category
- `level`: Difficulty level
- `timestamp`: Creation timestamp

**Content Distribution**:
- 5 subjects: Mathematics, Physics, Chemistry, Biology, Computer Science
- 3 difficulty levels: Elementary, Middle School, High School
- ~75 questions per subject (distributed across difficulty levels)

## Usage

### Import Questions
```bash
python migrate_questions.py
```

### Verify Import
After running migration, the system will show:
- Questions imported count
- Distribution by category and level
- Total questions available

## Migration Features

- ✅ **Duplicate Prevention**: Checks for existing questions before import
- 📊 **Progress Tracking**: Shows import progress every 50 questions
- 🔄 **Error Handling**: Continues import even if individual questions fail
- 📈 **Summary Report**: Shows final distribution after import
- 🛡️ **Transaction Safety**: Rolls back on critical errors

## File Maintenance

### Re-exporting Questions
If you need to update the CSV file:

1. **From pgAdmin**: Export question_bank table as CSV
2. **Replace file**: Copy new CSV to `migrations/question_bank.csv`
3. **Test import**: Run migration on test database first

### Adding New Questions
To add questions to the existing bank:

1. **Manual Addition**: Add directly to database via application
2. **CSV Import**: Add to CSV file and re-import
3. **Bulk Operations**: Use database tools for large additions

## Troubleshooting

### Common Issues

**File Not Found**:
```
❌ CSV file not found: migrations/question_bank.csv
```
Solution: Ensure CSV file exists in migrations folder

**Import Fails**:
```
❌ Error during import: [error message]
```
Solution: Check CSV format and database connection

**Duplicate Questions**:
- System warns before adding duplicates
- Choose 'N' to cancel or 'y' to continue

### Validation

The migration script validates:
- CSV file format and structure
- Database connectivity
- Question data integrity
- Required fields presence

## Security Notes

- CSV file contains educational content only
- No sensitive user data in migrations
- Safe to include in version control
- Questions are public educational material

---

**Note**: This migration system is designed for initial setup. For production updates, consider using proper database migration tools.