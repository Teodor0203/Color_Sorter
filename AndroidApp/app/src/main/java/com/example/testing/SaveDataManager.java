package com.example.testing;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.content.Context;
import android.text.InputType;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.fragment.app.FragmentActivity;
import androidx.fragment.app.FragmentTransaction;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public class SaveDataManager
{

    private static final String TAG = "SaveDataManager";

    private int countRed = 0;
    private int countBlue = 0;
    private int countYellow = 0;
    private int countPink = 0;

    private static SaveDataManager INSTANCE;


    public static SaveDataManager getInstance()
    {
        if (INSTANCE == null) {
            INSTANCE = new SaveDataManager();

        }
        return INSTANCE;
    }

    public void saveDataToFile(Context context, String fileName, int redCounter, int blueCounter, int yellowCounter, int pinkCounter)
    {
        try
        {
            JSONObject json = new JSONObject();

            json.put("red", redCounter);
            json.put("blue", blueCounter);
            json.put("yellow", yellowCounter);
            json.put("pink", pinkCounter);

            FileOutputStream fos = context.openFileOutput(fileName, Context.MODE_PRIVATE);
            fos.write(json.toString().getBytes());
            fos.close();

            FileOutputStream fos1 = context.openFileOutput("data.txt", Context.MODE_APPEND);
            fos1.write(("\n"+fileName).getBytes());
            fos1.close();

            Log.d(TAG, "Trail saved successfully to " + fileName);

            int index = loadIndexFromFile(context);
            index++;
            saveIndexToFile(context, index);
        } catch (Exception e) {
            Log.e("TrailManager", "Error saving trail: " + e.getMessage(), e);
        }
    }

    @SuppressLint("SetTextI18n")
    public void loadSavedData(Context context, String fileName, TextView redColor, TextView blueColor, TextView yellowColor, TextView pinkColor)
    {
        try
        {
            FileInputStream fis = context.openFileInput(fileName);
            BufferedReader reader = new BufferedReader(new InputStreamReader(fis));
            StringBuilder jsonBuilder = new StringBuilder();
            String line;

            while((line = reader.readLine()) != null)
            {
                jsonBuilder.append(line);
            }

            fis.close();

            JSONObject json = new JSONObject(jsonBuilder.toString());

            countRed = json.optInt("red", 0);
            countBlue = json.optInt("blue", 0);
            countYellow = json.optInt("yellow", 0);
            countPink = json.optInt("pink", 0);

            String fileRedObjects = json.has("red") ? String.valueOf(json.getInt("red")) : "NaN";
            String fileBlueObjects = json.has("blue") ? String.valueOf(json.getInt("blue")) : "NaN";
            String fileYellowObjects = json.has("yellow") ? String.valueOf(json.getInt("yellow")) : "NaN";
            String filePinkObjects = json.has("pink") ? String.valueOf(json.getInt("pink")) : "NaN";

            if (redColor != null && blueColor != null && yellowColor != null && pinkColor != null) {
                    redColor.setText("Red: " + fileRedObjects);
                    blueColor.setText("Blue: " + fileBlueObjects);
                    yellowColor.setText("Yellow: " + fileYellowObjects);
                    pinkColor.setText("Pink: " + filePinkObjects);
            }

            Log.d(TAG, "Loaded color counters from file: " + fileName);
        }
        catch (Exception e) {

            Log.e(TAG, "Error loading color counters with index: " + e.getMessage(), e);
            countRed = 0;
            countBlue = 0;
            countYellow = 0;
            countPink = 0;
        }
    }

    public int loadIndexFromFile(Context context)
    {
        int lastIndex = 1;

        try
        {
            FileInputStream fis = context.openFileInput("index.txt");
            BufferedReader reader = new BufferedReader(new InputStreamReader(fis));
            String line = reader.readLine();
            if(line != null)
            {
                lastIndex = Integer.parseInt(line);
                Log.d(TAG, "loadIndexFromFile: last index" + lastIndex);
            }
            fis.close();
        }
        catch (Exception e)
        {
            Log.e(TAG,"Error loading index: " + e.getMessage(), e);
        }

        return lastIndex;
    }

    private void saveIndexToFile(Context context, int index)
    {
        try
        {
            FileOutputStream fos = context.openFileOutput("index.txt", Context.MODE_PRIVATE);
            fos.write(Integer.toString(index).getBytes());
            fos.close();
        }
        catch (Exception e)
        {
            Log.e(TAG, "Error saving index: " + e.getMessage(), e);
        }
    }

    public void deleteFile(Context context, String trailName, Button buttonToRemove, LinearLayout savedDataContainer) {
        if (context == null) return;

        // Șterge fișierul efectiv
        File file = new File(context.getFilesDir(), trailName);
        if (file.exists()) file.delete();

        // Actualizează data.txt (fără linii goale)
        try {
            File dataFile = new File(context.getFilesDir(), "data.txt");
            List<String> lines = new ArrayList<>();
            BufferedReader reader = new BufferedReader(new FileReader(dataFile));
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (!line.equals(trailName) && !line.isEmpty()) {
                    lines.add(line);
                }
            }
            reader.close();

            FileWriter writer = new FileWriter(dataFile, false);

            writer.write("\n");

            for (int i = 0; i < lines.size(); i++) {
                writer.write(lines.get(i));
                if (i < lines.size() - 1) writer.write("\n");
            }
            writer.close();
        } catch (IOException e) {
            Log.e("DeleteTrail", "Error updating data.txt: " + e.getMessage());
        }

        savedDataContainer.removeView(buttonToRemove);
        Toast.makeText(context, "Deleted " + trailName, Toast.LENGTH_SHORT).show();

        // Reload fragment
        FragmentTransaction ft = ((FragmentActivity) context).getSupportFragmentManager().beginTransaction();
        ft.setReorderingAllowed(true)
                .setCustomAnimations(R.anim.fade_in, R.anim.fade_out)
                .replace(R.id.rootContainer, new FragmentSavedDataMenu())
                .commit();
    }


    public void showRenameDialog(Context context, String oldName, Button buttonToUpdate) {
        if (context == null) return;

        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle("Rename file");

        final EditText input = new EditText(context);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setText(oldName);
        builder.setView(input);

        builder.setPositiveButton("OK", (dialog, which) -> {
            String newName = input.getText().toString().trim();
            if (!newName.isEmpty() && !newName.equals(oldName)) {
                File oldFile = new File(context.getFilesDir(), oldName);
                File newFile = new File(context.getFilesDir(), newName);

                if (oldFile.exists() && !newFile.exists()) {
                    boolean success = oldFile.renameTo(newFile);
                    if (success) {
                        try {
                            File dataFile = new File(context.getFilesDir(), "data.txt");
                            List<String> lines = new ArrayList<>();
                            BufferedReader reader = new BufferedReader(new FileReader(dataFile));
                            String line;
                            while ((line = reader.readLine()) != null) {
                                line = line.trim();
                                if (line.equals(oldName)) {
                                    lines.add(newName);
                                } else if (!line.isEmpty()) {
                                    lines.add(line);
                                }
                            }
                            reader.close();

                            FileWriter writer = new FileWriter(dataFile, false);

                            writer.write("\n");

                            for (int i = 0; i < lines.size(); i++) {
                                writer.write(lines.get(i));
                                if (i < lines.size() - 1) writer.write("\n");
                            }
                            writer.close();
                        } catch (IOException e) {
                            Log.e("RenameTrail", "Error updating data.txt: " + e.getMessage());
                        }

                        buttonToUpdate.setText(newName);
                        Toast.makeText(context, "Renamed to " + newName, Toast.LENGTH_SHORT).show();

                        // Reload fragment
                        FragmentTransaction ft = ((FragmentActivity) context).getSupportFragmentManager().beginTransaction();
                        ft.setReorderingAllowed(true)
                                .setCustomAnimations(R.anim.fade_in, R.anim.fade_out)
                                .replace(R.id.rootContainer, new FragmentSavedDataMenu())
                                .commit();

                    } else {
                        Toast.makeText(context, "Rename failed", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Toast.makeText(context, "File doesn't exist or name already taken", Toast.LENGTH_SHORT).show();
                }
            }
        });

        builder.setNegativeButton("Cancel", (dialog, which) -> dialog.cancel());
        builder.show();
    }



}
